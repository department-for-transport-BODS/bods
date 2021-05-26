import clamd
import pytest
from clamd import ClamdNetworkSocket

from transit_odp.validate.antivirus import (
    SCAN_ATTEMPTS,
    AntiVirusError,
    ClamConnectionError,
    FileScanner,
    ScanResult,
    SuspiciousFile,
)

CLAMD = "transit_odp.validate.antivirus.ClamdNetworkSocket"
PERFORM_SCAN = "transit_odp.validate.antivirus.FileScanner._perform_scan"


class TestFileScanner:
    def get_mocked_scanner(self, mocker):
        host = "http://fakeclamavhost.com"
        port = 1234
        mclamd = mocker.patch(CLAMD)
        mclamd_ns = mocker.MagicMock(spec=ClamdNetworkSocket)
        mclamd.return_value = mclamd_ns
        scanner = FileScanner(host, port)
        return scanner

    def test_create_scanner(self, mocker):
        host = "http://fakeclamavhost.com"
        port = 1234
        mclamd = mocker.patch(CLAMD)
        mclamd_ns = mocker.MagicMock(spec=ClamdNetworkSocket)
        mclamd.return_value = mclamd_ns
        scanner = FileScanner(host, port)
        assert scanner.clamav == mclamd_ns

    def test_perform_scan(self, mocker):
        status = "FILE_FINE"
        reason = "a reason"
        av_response = {"stream": (status, reason)}
        mfile = mocker.MagicMock(name="suspiciousfile.txt")

        scanner = self.get_mocked_scanner(mocker)
        scanner.clamav.instream.return_value = av_response

        expected = ScanResult(status=status, reason=reason)
        actual = scanner._perform_scan(mfile)
        scanner.clamav.instream.assert_called_once_with(mfile)
        assert actual == expected

    @pytest.mark.parametrize(
        "side_effect, expected",
        [
            (clamd.BufferTooLongError, AntiVirusError),
            (clamd.ConnectionError, clamd.ConnectionError),
        ],
    )
    def test_perform_scan_exceptions(self, side_effect, expected, mocker):
        mfile = mocker.MagicMock(name="suspiciousfile.txt")
        scanner = self.get_mocked_scanner(mocker)
        scanner.clamav.instream.side_effect = side_effect
        with pytest.raises(expected):
            scanner._perform_scan(mfile)
        if side_effect == clamd.ConnectionError:
            assert scanner.clamav.instream.call_count == SCAN_ATTEMPTS

    def test_scan(self, mocker):
        mfile = mocker.MagicMock(name="suspiciousfile.txt")
        scanner = self.get_mocked_scanner(mocker)
        mperform_scan = mocker.patch(PERFORM_SCAN)
        mperform_scan.return_value = ScanResult(status="OK", reason="Everything OK")
        actual = scanner.scan(mfile)
        assert actual is None

    def test_scan_error(self, mocker):
        scanner = self.get_mocked_scanner(mocker)
        mperform_scan = mocker.patch(PERFORM_SCAN)
        mperform_scan.return_value = ScanResult(
            status="ERROR", reason="Antivirus scan Failed."
        )
        mfile = mocker.MagicMock(name="suspiciousfile.txt")
        with pytest.raises(AntiVirusError) as excinfo:
            scanner.scan(mfile)
        assert excinfo.value.filename == mfile.name

    def test_scan_found(self, mocker):
        scanner = self.get_mocked_scanner(mocker)
        mperform_scan = mocker.patch(PERFORM_SCAN)
        mperform_scan.return_value = ScanResult(
            status="FOUND", reason="Antivirus scan: Found."
        )
        mfile = mocker.MagicMock(name="suspiciousfile.txt")
        with pytest.raises(SuspiciousFile) as excinfo:
            scanner.scan(mfile)
        assert excinfo.value.filename == mfile.name

    def test_scan_connection_error(self, mocker):
        mperform_scan = mocker.patch(PERFORM_SCAN)
        mperform_scan.side_effect = clamd.ConnectionError
        mfile = mocker.MagicMock(name="suspiciousfile.txt")
        expected_msg = f"Could not connect to Clam daemon when testing {mfile.name}."
        scanner = self.get_mocked_scanner(mocker)

        with pytest.raises(ClamConnectionError) as excinfo:
            scanner.scan(mfile)

        assert excinfo.value.filename == mfile.name
        assert excinfo.value.code == "AV_CONNECTION_ERROR"
        assert excinfo.value.message == expected_msg

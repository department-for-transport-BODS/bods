import io
import zipfile

from django.core.files.base import ContentFile
from django.test import TestCase

from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.timetables.etl import TransXChangePipeline
from transit_odp.validate.utils import filter_and_repackage_zip


class TestFilterAndRepackageZip(TestCase):
    def setUp(self):
        self.revision = DatasetRevisionFactory(
            dataset__dataset_type=DatasetType.TIMETABLE.value
        )
        self.instance = TransXChangePipeline(revision=self.revision)

    def create_zip_with_files(self, file_contents):
        zip_stream = io.BytesIO()
        with zipfile.ZipFile(zip_stream, "w") as zf:
            for filename, content in file_contents.items():
                zf.writestr(filename, content)
        zip_stream.seek(0)
        return zip_stream

    def test_filter_and_repackage_zip(self):
        file_contents = {
            "file1.xml": "<root>Content1</root>",
            "failed_validations.xml": "<root>Failed Validations</root>",
            "file3.xml": "<root>Content3</root>",
        }
        input_zip = self.create_zip_with_files(file_contents)

        files_to_remove = ["failed_validations.xml"]

        output_zip_stream = filter_and_repackage_zip(input_zip, files_to_remove)

        with zipfile.ZipFile(output_zip_stream, "r") as output_zip:
            self.assertIn("file3.xml", output_zip.namelist())
            self.assertIn("file1.xml", output_zip.namelist())
            self.assertNotIn("failed_validations.xml", output_zip.namelist())
            self.assertEqual(
                output_zip.read("file3.xml").decode(), "<root>Content3</root>"
            )

    def test_no_files_to_remove(self):
        file_contents = {
            "file1.xml": "<root>Content1</root>",
            "file2.xml": "<root>Content2</root>",
        }
        input_zip = self.create_zip_with_files(file_contents)
        files_to_remove = []

        output_zip_stream = filter_and_repackage_zip(input_zip, files_to_remove)

        with zipfile.ZipFile(output_zip_stream, "r") as output_zip:
            self.assertIn("file1.xml", output_zip.namelist())
            self.assertIn("file2.xml", output_zip.namelist())

    def test_all_files_removed(self):
        file_contents = {
            "file1.xml": "<root>Content1</root>",
            "file2.xml": "<root>Content2</root>",
        }
        input_zip = self.create_zip_with_files(file_contents)
        files_to_remove = ["file1.xml", "file2.xml"]

        output_zip_stream = filter_and_repackage_zip(input_zip, files_to_remove)

        with zipfile.ZipFile(output_zip_stream, "r") as output_zip:
            self.assertEqual(output_zip.namelist(), [])

    def test_no_xml_files(self):
        file_contents = {
            "file1.txt": "Text file content",
            "file2.txt": "Another text file content",
        }
        input_zip = self.create_zip_with_files(file_contents)
        files_to_remove = []

        output_zip_stream = filter_and_repackage_zip(input_zip, files_to_remove)

        with zipfile.ZipFile(output_zip_stream, "r") as output_zip:
            self.assertEqual(output_zip.namelist(), [])

    def test_empty_input_zip(self):
        input_zip = io.BytesIO()
        with zipfile.ZipFile(input_zip, "w") as zf:
            pass

        input_zip.seek(0)
        files_to_remove = []

        output_zip_stream = filter_and_repackage_zip(input_zip, files_to_remove)

        with zipfile.ZipFile(output_zip_stream, "r") as output_zip:
            self.assertEqual(output_zip.namelist(), [])

    def test_invalid_zip(self):
        invalid_zip = io.BytesIO(b"not a zip file")

        with self.assertRaises(zipfile.BadZipFile):
            filter_and_repackage_zip(invalid_zip, [])

    def test_replace_zip_file(self):
        """
        Tests replacing the zip file in DatasetRevision table with the filtered version.
        """
        file_contents = {
            "file1.xml": "<root>Content1</root>",
            "failed_validations.xml": "<root>Failed Validations</root>",
            "file3.xml": "<root>Content3</root>",
        }
        initial_zip = self.create_zip_with_files(file_contents)
        files_to_remove = ["failed_validations.xml"]

        self.revision.upload_file = ContentFile(initial_zip.read(), name="test.zip")

        self.revision.modify_upload_file(files_to_remove)

        new_zip_content = self.revision.upload_file.read()
        new_zip_stream = io.BytesIO(new_zip_content)

        with zipfile.ZipFile(new_zip_stream, "r") as output_zip:
            namelist = output_zip.namelist()
            self.assertIn("file1.xml", namelist)
            self.assertNotIn("failed_validations.xml", namelist)
            self.assertIn("file3.xml", namelist)
            self.assertEqual(
                output_zip.read("file1.xml").decode(), "<root>Content1</root>"
            )
            self.assertEqual(
                output_zip.read("file3.xml").decode(), "<root>Content3</root>"
            )

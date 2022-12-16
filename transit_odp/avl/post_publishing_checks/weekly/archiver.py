import io
from typing import Protocol
from zipfile import ZIP_DEFLATED, ZipFile

from pandas import DataFrame

from transit_odp.avl.post_publishing_checks.weekly.constants import (
    README_INTRO,
    README_OUTRO,
    WeeklyPPCSummaryFiles,
)
from transit_odp.avl.post_publishing_checks.weekly.fields import (
    BLOCK_REF_FIELDS,
    DESTINATION_REF_FIELDS,
    DIRECTION_REF_FIELDS,
    ORIGIN_REF_FIELDS,
    SIRI_MSG_ANALYSED_FIELDS,
    UNCOUNTED_VEHICLE_ACTIVITIES_FIELDS,
)
from transit_odp.avl.post_publishing_checks.weekly.summary import PPC_SUMMARY_FIELDS


class WeeklyReport(Protocol):
    def get_summary_report(self) -> DataFrame:
        ...

    def get_siri_message_analysed(self) -> DataFrame:
        ...

    def get_uncounted_vehicle_activities(self) -> DataFrame:
        ...

    def get_direction_ref(self) -> DataFrame:
        ...

    def get_destination_ref(self) -> DataFrame:
        ...

    def get_origin_ref(self) -> DataFrame:
        ...

    def get_block_ref(self) -> DataFrame:
        ...


class WeeklyPPCReportArchiver:
    """Create Weekly Archive for PPC"""

    def to_zip(self, data: WeeklyReport):
        bytesio = io.BytesIO()

        with ZipFile(bytesio, "w", ZIP_DEFLATED) as archive:
            archive.writestr(
                WeeklyPPCSummaryFiles.PPC_SUMMARY_REPORT,
                data=data.get_summary_report().to_csv(index=False),
            )
            archive.writestr(
                WeeklyPPCSummaryFiles.BLOCK_REF,
                data=data.get_block_ref().to_csv(index=False),
            )
            archive.writestr(
                WeeklyPPCSummaryFiles.DESTINATION_REF,
                data=data.get_destination_ref().to_csv(index=False),
            )
            archive.writestr(
                WeeklyPPCSummaryFiles.DIRECTION_REF,
                data=data.get_direction_ref().to_csv(index=False),
            )
            archive.writestr(
                WeeklyPPCSummaryFiles.ORIGIN_REF,
                data=data.get_origin_ref().to_csv(index=False),
            )
            archive.writestr(
                WeeklyPPCSummaryFiles.SIRI_MESSAGE_ANALYSED,
                data=data.get_siri_message_analysed().to_csv(index=False),
            )
            archive.writestr(
                WeeklyPPCSummaryFiles.UNCOUNTED_VEHICLE_ACTIVITY,
                data=data.get_uncounted_vehicle_activities().to_csv(index=False),
            )
            archive.writestr(WeeklyPPCSummaryFiles.README, data=self._get_readme())

        return bytesio

    @staticmethod
    def _get_readme() -> str:
        row_template = "{field_name:45}{definition}"
        header_template = "{header}\n{field_header:45}Definition\n"
        field_header = "Field name"

        readme = [README_INTRO]

        locations = f"\n{WeeklyPPCSummaryFiles.PPC_SUMMARY_REPORT}"
        readme.append(
            header_template.format(header=locations, field_header=field_header)
        )
        readme += [
            row_template.format(field_name=field, definition=desc)
            for field, desc in PPC_SUMMARY_FIELDS.items()
        ]

        locations = f"\n{WeeklyPPCSummaryFiles.BLOCK_REF}"
        readme.append(
            header_template.format(header=locations, field_header=field_header)
        )
        readme += [
            row_template.format(field_name=field, definition=desc)
            for field, desc in BLOCK_REF_FIELDS.items()
        ]

        locations = f"\n{WeeklyPPCSummaryFiles.DESTINATION_REF}"
        readme.append(
            header_template.format(header=locations, field_header=field_header)
        )
        readme += [
            row_template.format(field_name=field, definition=desc)
            for field, desc in DESTINATION_REF_FIELDS.items()
        ]

        locations = f"\n{WeeklyPPCSummaryFiles.DIRECTION_REF}"
        readme.append(
            header_template.format(header=locations, field_header=field_header)
        )
        readme += [
            row_template.format(field_name=field, definition=desc)
            for field, desc in DIRECTION_REF_FIELDS.items()
        ]

        locations = f"\n{WeeklyPPCSummaryFiles.ORIGIN_REF}"
        readme.append(
            header_template.format(header=locations, field_header=field_header)
        )
        readme += [
            row_template.format(field_name=field, definition=desc)
            for field, desc in ORIGIN_REF_FIELDS.items()
        ]

        locations = f"\n{WeeklyPPCSummaryFiles.SIRI_MESSAGE_ANALYSED}"
        readme.append(
            header_template.format(header=locations, field_header=field_header)
        )
        readme += [
            row_template.format(field_name=field, definition=desc)
            for field, desc in SIRI_MSG_ANALYSED_FIELDS.items()
        ]

        locations = f"\n{WeeklyPPCSummaryFiles.UNCOUNTED_VEHICLE_ACTIVITY}"
        readme.append(
            header_template.format(header=locations, field_header=field_header)
        )
        readme += [
            row_template.format(field_name=field, definition=desc)
            for field, desc in UNCOUNTED_VEHICLE_ACTIVITIES_FIELDS.items()
        ]

        readme.append(README_OUTRO)
        return "\n".join(readme)

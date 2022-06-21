from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from django.http.response import FileResponse, Http404

from transit_odp.avl.managers import AVLDatasetManager, AVLDatasetRevisionManager
from transit_odp.avl.querysets import AVLDatasetQuerySet
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.organisation.querysets import DatasetRevisionQuerySet


class AVLDataset(Dataset):
    objects = AVLDatasetManager.from_queryset(AVLDatasetQuerySet)()

    class Meta:
        proxy = True

    def to_validation_reports_response(self):
        org_name = self.organisation.name
        revision = self.live_revision
        reports = revision.avl_validation_reports.all().order_by("-created")[:7]
        reports = [
            r
            for r in reports
            if r.file and (r.critical_count > 0 or r.non_critical_count > 0)
        ]

        created = reports[0].created
        buffer_ = BytesIO()
        with ZipFile(buffer_, "w", compression=ZIP_DEFLATED) as zin:
            for report in reports:
                zin.writestr(report.file.name, report.file.read())
        buffer_.seek(0)

        filename = f"BODS_SIRI_validation_{org_name}_{created:%d%m%Y}.zip"
        response = FileResponse(buffer_, as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    def to_schema_validation_response(self):
        org_name = self.organisation.name
        revision = self.live_revision
        report = revision.avl_schema_validation_reports.order_by("-created").first()

        if report is None:
            raise Http404

        filename = f"BODS_Schema_validation_{org_name}_{report.created:%d%m%Y}.csv"
        response = FileResponse(report.file.open("rb"), as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response


class AVLDatasetRevision(DatasetRevision):
    objects = AVLDatasetRevisionManager.from_queryset(DatasetRevisionQuerySet)

    class Meta:
        proxy = True

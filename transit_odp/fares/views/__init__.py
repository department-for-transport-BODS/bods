from .archive import FaresFeedArchiveSuccessView, FaresFeedArchiveView
from .changelog import FaresChangelogView
from .create import FaresUploadWizard
from .delete import RevisionDeleteFaresView, RevisionDeleteSuccessView
from .detail import FaresFeedDetailView
from .download import DownloadFaresFileView
from .list import ListView
from .review import (
    FaresDatasetUploadModify,
    ReviewView,
    RevisionPublishSuccessView,
    UpdateRevisionPublishView,
)
from .update import (
    DatasetUpdateModify,
    DraftExistsView,
    FeedUpdateWizard,
    RevisionUpdateSuccessView,
)

__all__ = [
    "ListView",
    "FaresUploadWizard",
    "ReviewView",
    "RevisionPublishSuccessView",
    "FaresFeedDetailView",
    "RevisionDeleteFaresView",
    "RevisionDeleteSuccessView",
    "FeedUpdateWizard",
    "DraftExistsView",
    "RevisionUpdateSuccessView",
    "DatasetUpdateModify",
    "UpdateRevisionPublishView",
    "FaresDatasetUploadModify",
    "FaresChangelogView",
    "FaresFeedArchiveSuccessView",
    "FaresFeedArchiveView",
    "DownloadFaresFileView",
]

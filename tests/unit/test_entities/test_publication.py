from django.utils.timezone import now
from freezegun import freeze_time

from transit_odp.bods.domain import events
from transit_odp.bods.domain.entities import AVLDataset, AVLPublication, Revision
from transit_odp.bods.domain.entities.identity import (
    OrganisationId,
    PublicationId,
    UserId,
)
from transit_odp.organisation.constants import AVLFeedStatus

NOW = now()


def test_records_status_changed_event():
    publication = AVLPublication(
        id=PublicationId(id=1),
        organisation_id=OrganisationId(id=1),
        contact_user_id=UserId(id=1),
        feed_status=AVLFeedStatus.DEPLOYING,
        feed_last_checked=None,
        live=Revision[AVLDataset](
            created_at=NOW,
            published_at=None,
            published_by=None,
            has_error=False,
            dataset=AVLDataset(
                name="Test Feed",
                description="Descriptive text",
                short_description="Short description",
                comment="Initial publication",
                url="http://www.test-feed.com",
                username="account123",
                password="password123",
                requestor_ref="",
            ),
        ),
        draft=None,
        events=[],
    )

    with freeze_time(NOW):
        publication.update_feed_status(status=AVLFeedStatus.FEED_DOWN)

    assert publication.feed_status == AVLFeedStatus.FEED_DOWN
    assert publication.feed_last_checked == NOW
    assert publication.events[-1] == events.AVLFeedStatusChanged(
        publication_id=publication.id, status=AVLFeedStatus.FEED_DOWN
    )

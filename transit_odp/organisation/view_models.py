from typing import Optional

import attr

from transit_odp.users.models import Invitation, User


@attr.s(auto_attribs=True)
class GlobalFeedStats(object):
    line_count: int
    feed_warnings: int
    total_dataset_count: int
    total_fare_products: int


@attr.s(auto_attribs=True)
class UserOrInvited(object):
    # A user or prospective user
    id: int
    email: str
    active: bool
    user: Optional[User]
    invitation: Optional[Invitation]
    account_type: int

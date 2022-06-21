import attr


@attr.s(auto_attribs=True)
class GlobalFeedStats:
    line_count: int
    feed_warnings: int
    total_dataset_count: int
    total_fare_products: int

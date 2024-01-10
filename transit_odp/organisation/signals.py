from django.dispatch import Signal

feed_expired = Signal()  # providing args ["dataset"]
feed_expiring = Signal()  # providing args ["dataset"]

feed_monitor_fail_first_try = Signal()  # providing args ["dataset"]
feed_monitor_fail_final_try = Signal()  # providing args ["dataset"]

feed_monitor_dataset_available = Signal()  # providing args ["dataset"]

revision_publish = Signal()  # providing args ["dataset"]

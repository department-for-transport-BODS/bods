from django.dispatch import Signal

feed_expired = Signal(["dataset"])
feed_expiring = Signal(["dataset"])

feed_monitor_fail_first_try = Signal(["dataset"])
feed_monitor_fail_final_try = Signal(["dataset"])

feed_monitor_dataset_available = Signal(["dataset"])

revision_publish = Signal(["dataset"])

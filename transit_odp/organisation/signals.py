from django.dispatch import Signal

feed_expired = Signal()
feed_expiring = Signal()

feed_monitor_fail_first_try = Signal()
feed_monitor_fail_final_try = Signal()

feed_monitor_dataset_available = Signal()

revision_publish = Signal()

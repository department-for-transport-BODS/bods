from django.dispatch import Signal

feed_expired = Signal(providing_args=["dataset"])
feed_expiring = Signal(providing_args=["dataset"])

feed_monitor_fail_first_try = Signal(providing_args=["dataset"])
feed_monitor_fail_final_try = Signal(providing_args=["dataset"])

feed_monitor_change_detected = Signal(providing_args=["dataset"])
feed_monitor_dataset_available = Signal(providing_args=["dataset"])

revision_publish = Signal(providing_args=["dataset"])

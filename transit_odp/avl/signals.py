from django.db.models.signals import post_delete
from django.dispatch import receiver

from transit_odp.avl.models import PostPublishingCheckReport


@receiver(post_delete, sender=PostPublishingCheckReport)
def post_delete_ppc_report(sender, instance, **kwargs):
    if instance.file.name:
        instance.file.delete(instance.file.name)

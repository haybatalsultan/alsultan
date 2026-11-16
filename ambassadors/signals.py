from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from ambassadors.models import AmbassadorProfile
from orders.models import Order


@receiver(post_save, sender=User)
def create_customer_ambassador_profile(sender, instance, created, **kwargs):
    if instance.role == User.Role.CUSTOMER:
        AmbassadorProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Order)
def reconcile_order_referral(sender, instance, **kwargs):
    from ambassadors.services.program import (
        reconcile_order_redemptions,
        reconcile_referral,
    )

    reconcile_referral(instance)
    reconcile_order_redemptions(instance)

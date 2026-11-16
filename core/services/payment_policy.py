from dataclasses import dataclass

from django.conf import settings

from core.models import StoreSetting


@dataclass(frozen=True)
class PaymentPolicy:
    online: bool
    manual: bool
    stripe_configured: bool

    @property
    def both(self) -> bool:
        return self.online and self.manual


def current_payment_policy() -> PaymentPolicy:
    """Return the effective customer payment policy without creating database rows."""
    stripe_configured = bool(settings.STRIPE_ENABLED)
    store = (
        StoreSetting.objects.filter(singleton=True)
        .only("online_payment_enabled", "whatsapp_checkout_enabled")
        .first()
    )
    if store is None:
        # Preserve the existing behavior until the Owner explicitly saves a policy.
        return PaymentPolicy(
            online=stripe_configured,
            manual=True,
            stripe_configured=stripe_configured,
        )
    return PaymentPolicy(
        online=bool(store.online_payment_enabled and stripe_configured),
        manual=bool(store.whatsapp_checkout_enabled),
        stripe_configured=stripe_configured,
    )

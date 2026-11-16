from accounts.models import MFADevice

TEST_MFA_SECRET = "JBSWY3DPEHPK3PXP"


def enable_management_mfa(user):
    device, _ = MFADevice.objects.get_or_create(
        user=user,
        defaults={"secret": TEST_MFA_SECRET, "enabled": True},
    )
    if not device.enabled:
        device.secret = device.secret or TEST_MFA_SECRET
        device.enabled = True
        device.save(update_fields=["secret", "enabled"])
    return device


def login_management(client, user, password):
    enable_management_mfa(user)
    ok = client.login(username=user.username, password=password)
    if not ok:
        raise AssertionError(f"Unable to log in test management user {user.username}")
    session = client.session
    session["mfa_verified_user_id"] = str(user.pk)
    session.save()
    return user

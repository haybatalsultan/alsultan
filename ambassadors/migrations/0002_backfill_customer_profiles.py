from django.db import migrations


def backfill(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Profile = apps.get_model("ambassadors", "AmbassadorProfile")
    from ambassadors.models import generate_ambassador_code

    for user_id in (
        User.objects.filter(role="CUSTOMER").values_list("id", flat=True).iterator()
    ):
        if not Profile.objects.filter(user_id=user_id).exists():
            for _ in range(10):
                code = generate_ambassador_code()
                if not Profile.objects.filter(code=code).exists():
                    Profile.objects.create(user_id=user_id, code=code)
                    break


class Migration(migrations.Migration):
    dependencies = [("ambassadors", "0001_initial")]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]

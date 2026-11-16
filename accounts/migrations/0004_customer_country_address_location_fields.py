from django.db import migrations, models
from django.db.models import Q


def normalize_default_addresses(apps, schema_editor):
    Address = apps.get_model("accounts", "Address")
    user_ids = (
        Address.objects.filter(is_default=True)
        .values_list("user_id", flat=True)
        .distinct()
    )
    for user_id in user_ids:
        defaults = list(
            Address.objects.filter(user_id=user_id, is_default=True)
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)
        )
        if len(defaults) > 1:
            Address.objects.filter(id__in=defaults[1:]).update(is_default=False)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_alter_user_groups_alter_user_is_active")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="country",
            field=models.CharField(db_index=True, default="AE", max_length=2),
        ),
        migrations.AlterField(
            model_name="address",
            name="emirate",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="address",
            name="city",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="address",
            name="postal_code",
            field=models.CharField(blank=True, max_length=24),
        ),
        migrations.RunPython(normalize_default_addresses, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="address",
            constraint=models.UniqueConstraint(
                fields=("user",),
                condition=Q(is_default=True),
                name="one_default_address_per_user",
            ),
        ),
    ]

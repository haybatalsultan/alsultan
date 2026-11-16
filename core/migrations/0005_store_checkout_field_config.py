from django.db import migrations, models

import core.services.checkout_fields


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_merge_20260822_2255"),
    ]

    operations = [
        migrations.AddField(
            model_name="storesetting",
            name="checkout_field_config",
            field=models.JSONField(
                blank=True,
                default=core.services.checkout_fields.default_checkout_field_config,
            ),
        ),
    ]

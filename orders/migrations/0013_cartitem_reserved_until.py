from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0012_ordernotification"),
    ]

    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="reserved_until",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]

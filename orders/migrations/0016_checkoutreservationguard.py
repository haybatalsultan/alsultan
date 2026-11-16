from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0015_reservation_limit_request")]
    operations = [
        migrations.CreateModel(
            name="CheckoutReservationGuard",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "identity_key",
                    models.CharField(db_index=True, max_length=96, unique=True),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]

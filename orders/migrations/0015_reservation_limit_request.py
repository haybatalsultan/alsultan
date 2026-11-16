import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0014_reservation_limit_override")]
    operations = [
        migrations.CreateModel(
            name="ReservationLimitRequest",
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
                ("requested_items", models.PositiveSmallIntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                            ("EXPIRED", "Expired"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=16,
                    ),
                ),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("admin_notified_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "cart",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reservation_limit_requests",
                        to="orders.cart",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_reservation_limit_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reservation_limit_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="reservationlimitrequest",
            index=models.Index(
                fields=["status", "created_at"], name="reservation_req_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="reservationlimitrequest",
            index=models.Index(
                fields=["user", "status"], name="reservation_req_user_idx"
            ),
        ),
    ]

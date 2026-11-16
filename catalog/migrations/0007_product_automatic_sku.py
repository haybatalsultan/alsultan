from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "catalog",
            "0006_rename_catalog_pro_status_00bc1c_idx_catalog_pro_status_9b3667_idx_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="sku",
            field=models.CharField(
                blank=True,
                db_index=True,
                editable=False,
                max_length=64,
                null=True,
                unique=True,
            ),
        ),
    ]

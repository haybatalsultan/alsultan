from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_master_data_fields")]

    operations = [
        migrations.AddField(
            model_name="productimage",
            name="cloudinary_asset_id",
            field=models.CharField(blank=True, db_index=True, max_length=80),
        ),
        migrations.AddField(
            model_name="productimage",
            name="width",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="productimage",
            name="height",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="productimage",
            name="bytes",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="productimage",
            name="format",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AlterModelOptions(
            name="productimage",
            options={"ordering": ["-is_primary", "sort_order", "id"]},
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_productimage_cloudinary_metadata")]

    operations = [
        migrations.AddField(
            model_name="category",
            name="image_public_id",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="material",
            name="image_url",
            field=models.URLField(blank=True, max_length=700),
        ),
        migrations.AddField(
            model_name="material",
            name="image_public_id",
            field=models.CharField(blank=True, max_length=300),
        ),
    ]

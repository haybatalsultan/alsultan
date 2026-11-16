from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_product_reference")]

    operations = [
        migrations.AddField(
            model_name="category",
            name="sort_order",
            field=models.PositiveSmallIntegerField(db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(editable=False, max_length=140, unique=True),
        ),
        migrations.AlterModelOptions(
            name="category",
            options={"ordering": ["sort_order", "name_en", "id"]},
        ),
        migrations.AddField(
            model_name="material",
            name="is_active",
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AddField(
            model_name="material",
            name="sort_order",
            field=models.PositiveSmallIntegerField(db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name="material",
            name="slug",
            field=models.SlugField(editable=False, max_length=140, unique=True),
        ),
        migrations.AlterModelOptions(
            name="material",
            options={"ordering": ["sort_order", "name_en", "id"]},
        ),
    ]

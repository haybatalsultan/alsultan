from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("catalog", "0005_master_data_cloudinary_images")]

    operations = [
        migrations.RenameIndex(
            model_name="product",
            new_name="catalog_pro_status_9b3667_idx",
            old_name="catalog_pro_status_00bc1c_idx",
        ),
        migrations.RenameIndex(
            model_name="product",
            new_name="catalog_pro_is_feat_e144de_idx",
            old_name="catalog_pro_is_feat_9c07e4_idx",
        ),
    ]

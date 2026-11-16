from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[("core","0006_invoice_identity_settings")]
    operations=[migrations.AddField(model_name="storesetting",name="bead_adjustment_enabled",field=models.BooleanField(default=False))]

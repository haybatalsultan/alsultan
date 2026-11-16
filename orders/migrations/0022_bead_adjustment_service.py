from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("orders","0021_invoice_snapshots"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
      migrations.AddField(model_name="cartitem",name="requested_bead_count",field=models.PositiveSmallIntegerField(blank=True,null=True)),
      migrations.AddField(model_name="orderitem",name="original_bead_count_snapshot",field=models.PositiveSmallIntegerField(blank=True,null=True)),
      migrations.AddField(model_name="orderitem",name="requested_bead_count_snapshot",field=models.PositiveSmallIntegerField(blank=True,null=True)),
      migrations.AddField(model_name="orderitem",name="bead_adjustment_completed_at",field=models.DateTimeField(blank=True,null=True)),
      migrations.AddField(model_name="orderitem",name="bead_adjustment_completed_by",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name="completed_bead_adjustments",to=settings.AUTH_USER_MODEL)),
      migrations.AddField(model_name="invoiceitem",name="original_bead_count_snapshot",field=models.PositiveSmallIntegerField(blank=True,null=True)),
      migrations.AddField(model_name="invoiceitem",name="requested_bead_count_snapshot",field=models.PositiveSmallIntegerField(blank=True,null=True)),
    ]

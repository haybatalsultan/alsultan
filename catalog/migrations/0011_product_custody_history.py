from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[('catalog','0010_public_hs_sku'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(name='ProductCustodyHistory',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('location_name',models.CharField(max_length=160)),('holder_name',models.CharField(blank=True,max_length=160)),('placed_on',models.DateField(db_index=True)),('note',models.CharField(blank=True,max_length=500)),('created_at',models.DateTimeField(auto_now_add=True,db_index=True)),('product',models.ForeignKey(on_delete=models.PROTECT,related_name='custody_history',to='catalog.product')),('recorded_by',models.ForeignKey(on_delete=models.PROTECT,related_name='product_custody_entries',to=settings.AUTH_USER_MODEL))])]

from django.db import models

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255, blank=True, null=True)
    market = models.CharField(max_length=40)
    product_image = models.CharField(max_length=255, blank=True, null=True)
    tags = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('product_name', 'market')
        db_table = 'products' 

    def __str__(self):
        return f"{self.product_name} ({self.market})"


class Price(models.Model):
    price_id = models.AutoField(primary_key=True)
    market = models.CharField(max_length=40)
    product_name = models.CharField(max_length=255)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id')
    special_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    regular_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_date = models.DateTimeField(auto_now_add=True)
    campaign = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'prices'

    def __str__(self):
        return f"{self.product_name} - {self.regular_price} ({self.price_date.strftime('%Y-%m-%d')})"
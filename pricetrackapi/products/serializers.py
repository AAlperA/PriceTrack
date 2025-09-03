from rest_framework import serializers
from .models import Product, Price

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'market',
            'brand', 
            'product_name', 
            'product_id',
            'product_image',
            'tags'
            ]

class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = [
            'product_id',
            'price_id',
            'special_price',
            'regular_price',
            'price_date',
            'campaign'
            ]

class NestedSerializer(serializers.ModelSerializer):
    prices = PriceSerializer(read_only=True) 

    class Meta:
        model = Product
        fields = [
            'product_id',
            'product_name',
            'market',
            'product_image',
            'tags',
            'prices'
        ]
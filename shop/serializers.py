from rest_framework import serializers
from django.db import transaction
from .models import Category, Product, Sale, SaleItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "category", "price", "quantity_in_stock"]

class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ["id", "product", "quantity", "price"]
        read_only_fields = ["price"]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)

    class Meta:
        model = Sale
        fields = ["id", "created_at", "total", "items"]
        read_only_fields = ["total", "created_at"]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("A sale needs at least one item.")
        return items

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        sale = Sale.objects.create(**validated_data)
        total = 0
        for item in items_data:
            product = Product.objects.select_for_update().get(pk=item["product"].pk)
            qty = item["quantity"]
            if qty > product.quantity_in_stock:
                raise serializers.ValidationError(
                    f"Not enough stock for {product.name}. Only {product.quantity_in_stock} left."
                )
            product.quantity_in_stock -= qty
            product.save()
            SaleItem.objects.create(
                sale=sale, product=product, quantity=qty, price=product.price
            )
            total += product.price * qty
        sale.total = total
        sale.save()
        return sale
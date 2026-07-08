from rest_framework import serializers

from .models import Item, ItemCategory


class ItemCategorySerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = ItemCategory
        fields = ["category_id", "name"]
        read_only_fields = ["category_id"]


class ItemSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(source="id", read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ItemCategory.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    category = ItemCategorySerializer(read_only=True)

    class Meta:
        model = Item
        fields = [
            "item_id",
            "name",
            "description",
            "category_id",
            "category",
            "quantity",
            "unit",
            "image_url",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["item_id", "category", "created_at"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("quantity must be greater than zero")
        return value


class ItemSearchSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(source="id", read_only=True)
    category = ItemCategorySerializer(read_only=True)

    class Meta:
        model = Item
        fields = [
            "item_id",
            "name",
            "description",
            "category",
            "quantity",
            "unit",
            "image_url",
            "is_active",
            "created_at",
        ]

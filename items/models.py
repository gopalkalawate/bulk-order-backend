from django.db import models
from django.contrib.postgres.indexes import GinIndex, OpClass
from django.contrib.postgres.search import SearchVectorField


class ItemCategory(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="category_id")
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = "item_categories"
        ordering = ["name"]
        verbose_name = "Item Category"
        verbose_name_plural = "Item Categories"

    def __str__(self):
        return self.name


class Item(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="item_id")
    name = models.CharField(max_length=255,unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        related_name="items",
        blank=True,
        null=True,
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=50, default="unit")
    # TODO: Accept uploaded item images, store them on S3, and persist the resulting S3 URL here.
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    search_vector = SearchVectorField(blank=True, null=True, editable=False)

    class Meta:
        db_table = "items"
        ordering = ["name"]
        verbose_name = "Item"
        verbose_name_plural = "Items"
        indexes = [
            GinIndex(fields=["search_vector"], name="idx_items_search"),
            GinIndex(OpClass("name", name="gin_trgm_ops"), name="idx_items_name_trgm"),
            GinIndex(OpClass("description", name="gin_trgm_ops"), name="idx_items_desc_trgm"),
            models.Index(fields=["category"], name="idx_items_category"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name="item_quantity_gt_zero",
            )
        ]

    def __str__(self):
        return self.name

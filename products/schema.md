Category
    │
    ▼
MasterProduct
(id, name, category_id)
    │
    ▼
Product (Sellable SKU)
(id, name, master_product_id,
 brand_id, cost(per unit), GST, quantity)

Brand
(id, name)

SearchIndex
(product_id, brand_id, text)
text-> apply full text search on this with GIN index and postgress trigram search 
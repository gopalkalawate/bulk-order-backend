# API Endpoints

## Ordering

All ordering endpoints require JWT authentication.

Header:

```http
Authorization: Bearer <ACCESS_TOKEN>
```

### Create Order Cycle

`POST /order-cycles` — ADMIN only.

Request body:

```json
{
  "service_location_id": 1,
  "cycle_date": "2026-07-20",
  "order_window_start": "2026-07-20T08:00:00Z",
  "order_window_end": "2026-07-20T12:00:00Z",
  "quote_window_end": "2026-07-20T15:00:00Z"
}
```

Curl:

```bash
curl -X POST "http://127.0.0.1:8000/order-cycles" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "service_location_id": 1,
    "cycle_date": "2026-07-20",
    "order_window_start": "2026-07-20T08:00:00Z",
    "order_window_end": "2026-07-20T12:00:00Z",
    "quote_window_end": "2026-07-20T15:00:00Z"
  }'
```

### Get Current Order Cycle

`GET /order-cycles/current` — CUSTOMER only. Uses the caller's assigned service location.

```bash
curl -X GET "http://127.0.0.1:8000/order-cycles/current" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Get Order Cycle

`GET /order-cycles/<cycle_id>` — ADMIN or a customer at that cycle's service location.

```bash
curl -X GET "http://127.0.0.1:8000/order-cycles/1" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Close Order Cycle

`POST /order-cycles/<cycle_id>/close` — ADMIN only. Snapshots confirmed orders and creates eligible vendor quote invitations.

```bash
curl -X POST "http://127.0.0.1:8000/order-cycles/1/close" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Select Lowest Quotes

`POST /order-cycles/<cycle_id>/select-lowest-quotes` — ADMIN only. Selects the lowest submitted quote that can fully supply each item and creates purchase orders.

```bash
curl -X POST "http://127.0.0.1:8000/order-cycles/1/select-lowest-quotes" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Get Cart

`GET /order-cycles/<cycle_id>/cart` — CUSTOMER only.

```bash
curl -X GET "http://127.0.0.1:8000/order-cycles/1/cart" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Add Cart Item

`POST /order-cycles/<cycle_id>/cart/items` — CUSTOMER only. Adding the same item replaces its quantity and notes.

Request body:

```json
{
  "item_id": 1,
  "quantity": "2.50",
  "notes": "Prefer small grains"
}
```

```bash
curl -X POST "http://127.0.0.1:8000/order-cycles/1/cart/items" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"item_id": 1, "quantity": "2.50", "notes": "Prefer small grains"}'
```

### Update or Remove Cart Item

`PATCH /order-cycles/<cycle_id>/cart/items/<item_id>` and `DELETE /order-cycles/<cycle_id>/cart/items/<item_id>` — CUSTOMER only.

```bash
curl -X PATCH "http://127.0.0.1:8000/order-cycles/1/cart/items/1" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"quantity": "3.00"}'

curl -X DELETE "http://127.0.0.1:8000/order-cycles/1/cart/items/1" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Checkout Cart and Get Orders

`POST /order-cycles/<cycle_id>/checkout` confirms the active cart. `GET /orders?cycle_id=1` lists the caller's orders. Both are CUSTOMER-only.

```bash
curl -X POST "http://127.0.0.1:8000/order-cycles/1/checkout" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

curl -X GET "http://127.0.0.1:8000/orders?cycle_id=1" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Vendor Quote Endpoints

Linked PARTNER users may read their invitations, replace draft quote lines, and submit before the quote deadline.

```bash
curl -X GET "http://127.0.0.1:8000/vendor-quotes" \
  -H "Authorization: Bearer <PARTNER_ACCESS_TOKEN>"

curl -X GET "http://127.0.0.1:8000/vendor-quotes/1" \
  -H "Authorization: Bearer <PARTNER_ACCESS_TOKEN>"
```

`PUT /vendor-quotes/<quote_id>/items` replaces all current draft lines.

Request body:

```json
[
  {"item_id": 1, "unit_price": "42.50", "available_quantity": "25.00"},
  {"item_id": 2, "unit_price": "18.00"}
]
```

```bash
curl -X PUT "http://127.0.0.1:8000/vendor-quotes/1/items" \
  -H "Authorization: Bearer <PARTNER_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '[
    {"item_id": 1, "unit_price": "42.50", "available_quantity": "25.00"},
    {"item_id": 2, "unit_price": "18.00"}
  ]'

curl -X POST "http://127.0.0.1:8000/vendor-quotes/1/submit" \
  -H "Authorization: Bearer <PARTNER_ACCESS_TOKEN>"
```

### Get Purchase Orders

`GET /purchase-orders?cycle_id=1` — ADMIN sees all POs; a linked PARTNER sees only their vendor's POs.

```bash
curl -X GET "http://127.0.0.1:8000/purchase-orders?cycle_id=1" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Configure Vendor Partner and Eligible Items

These endpoints are ADMIN-only. A linked user must have role `PARTNER`.

```bash
curl -X POST "http://127.0.0.1:8000/vendors/1/partner" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"partner_user_id": "<PARTNER_USER_UUID>"}'

curl -X POST "http://127.0.0.1:8000/vendors/1/items" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"item_id": 1}'

curl -X DELETE "http://127.0.0.1:8000/vendors/1/items/1" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Items

All item endpoints require JWT authentication.

Header:

```http
Authorization: Bearer <ACCESS_TOKEN>
```

### Create Item Category

`POST /items/create-category`

Request body:

```json
{
  "name": "Vegetables"
}
```

Example response:

```json
{
  "category_id": 1,
  "name": "Vegetables"
}
```

Curl:

```bash
curl -X POST "http://127.0.0.1:8000/items/create-category" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vegetables"
  }'
```

### Create Item

`POST /items/create-item`

Creates a catalog item. `quantity` must be greater than zero. `image_url` is accepted for now; uploaded image-to-S3 handling will be added later.

Request body:

```json
{
  "name": "Tomato",
  "description": "Fresh red tomato",
  "category_id": 1,
  "quantity": "5.50",
  "unit": "kg",
  "image_url": "https://example.com/tomato.jpg"
}
```

Example response:

```json
{
  "item_id": 1,
  "name": "Tomato",
  "description": "Fresh red tomato",
  "category": {
    "category_id": 1,
    "name": "Vegetables"
  },
  "quantity": "5.50",
  "unit": "kg",
  "image_url": "https://example.com/tomato.jpg",
  "is_active": true,
  "created_at": "2026-07-09T12:00:00Z"
}
```

Curl:

```bash
curl -X POST "http://127.0.0.1:8000/items/create-item" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tomato",
    "description": "Fresh red tomato",
    "category_id": 1,
    "quantity": "5.50",
    "unit": "kg",
    "image_url": "https://example.com/tomato.jpg"
  }'
```

### Search Items

`GET /items/search?q=tomto&category_id=1&is_active=true&limit=20`

Searches catalog items with PostgreSQL full-text search plus trigram fuzzy matching for typo tolerance.

Query params:

```text
q=rice
category_id=1
is_active=true
limit=20
```

Curl:

```bash
curl -X GET "http://127.0.0.1:8000/items/search?q=tomato&category_id=1&is_active=true&limit=20" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Update Item

`PATCH /items/<item_id>`

Partially updates an item.

Request body:

```json
{
  "quantity": "7.25",
  "image_url": "https://example.com/new-tomato.jpg"
}
```

Curl:

```bash
curl -X PATCH "http://127.0.0.1:8000/items/1" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": "7.25",
    "image_url": "https://example.com/new-tomato.jpg"
  }'
```

## Vendors

All vendor endpoints require JWT authentication.

Header:

```http
Authorization: Bearer <ACCESS_TOKEN>
```

### Create Vendor

`POST /vendors/create_vendor`

Creates a vendor. `latitude` and `longitude` are optional, but must be provided together when included.

Request body:

```json
{
  "name": "Fresh Supply Co",
  "email": "vendor@example.com",
  "phone": "9876543210",
  "latitude": 18.5204,
  "longitude": 73.8567
}
```

Example response:

```json
{
  "id": 1,
  "name": "Fresh Supply Co",
  "email": "vendor@example.com",
  "phone": "9876543210",
  "location_latitude": 18.5204,
  "location_longitude": 73.8567,
  "home_service_location_id": null,
  "home_service_location_name": null,
  "is_active": true,
  "created_at": "2026-07-04T12:00:00Z"
}
```

Curl:

```bash
curl -X POST "http://127.0.0.1:8000/vendors/create_vendor" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fresh Supply Co",
    "email": "vendor@example.com",
    "phone": "9876543210",
    "latitude": 18.5204,
    "longitude": 73.8567
  }'
```

### Set Vendor Location

`POST /vendors/set-vendor-location`

Sets the vendor's own/home service location. This also adds that location to the vendor's serviceable locations. `latitude` and `longitude` are optional, but must be provided together when included.

Request body:

```json
{
  "vendor_id": 1,
  "service_location_id": 2,
  "latitude": 18.5204,
  "longitude": 73.8567
}
```

Example response:

```json
{
  "id": 1,
  "name": "Fresh Supply Co",
  "email": "vendor@example.com",
  "phone": "9876543210",
  "location_latitude": 18.5204,
  "location_longitude": 73.8567,
  "home_service_location_id": 2,
  "home_service_location_name": "Pune Central",
  "is_active": true,
  "created_at": "2026-07-04T12:00:00Z"
}
```

Curl:

```bash
curl -X POST "http://127.0.0.1:8000/vendors/set-vendor-location" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": 1,
    "service_location_id": 2,
    "latitude": 18.5204,
    "longitude": 73.8567
  }'
```

### Get Vendor Service Locations

`GET /vendors/get-service-locations?vendor_id=1`

Returns active platform service locations within 20km of the vendor's saved PostGIS location.

Query params:

```text
vendor_id=1
```

Example response:

```json
[
  {
    "id": 2,
    "name": "Pune Central",
    "distance_km": 0.0,
    "is_active": true,
    "is_home_location": true,
    "is_already_serviceable": true
  }
]
```

Curl:

```bash
curl -X GET "http://127.0.0.1:8000/vendors/get-service-locations?vendor_id=1" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Add Serviceable Location

`POST /vendors/add-serviceable-location`

Adds a service location to the vendor's serviceable location set. The operation is idempotent.

Request body:

```json
{
  "vendor_id": 1,
  "service_location_id": 3
}
```

Example response:

```json
{
  "id": 5,
  "vendor": {
    "id": 1,
    "name": "Fresh Supply Co",
    "email": "vendor@example.com",
    "phone": "9876543210",
    "location_latitude": 18.5204,
    "location_longitude": 73.8567,
    "home_service_location_id": 2,
    "home_service_location_name": "Pune Central",
    "is_active": true,
    "created_at": "2026-07-04T12:00:00Z"
  },
  "service_location": {
    "id": 3,
    "name": "Pune West",
    "is_active": true
  }
}
```

Curl:

```bash
curl -X POST "http://127.0.0.1:8000/vendors/add-serviceable-location" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": 1,
    "service_location_id": 3
  }'
```

### Remove Serviceable Location

`POST /vendors/remove-serviceable-location`

Removes a serviceable location from a vendor. The vendor's own/home service location cannot be removed.

Request body:

```json
{
  "vendor_id": 1,
  "service_location_id": 3
}
```

Successful response:

```text
204 No Content
```

Home-location error response:

```json
{
  "error": "Vendor home service location cannot be removed"
}
```

Curl:

```bash
curl -X POST "http://127.0.0.1:8000/vendors/remove-serviceable-location" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": 1,
    "service_location_id": 3
  }'
```

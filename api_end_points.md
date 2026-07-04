# API Endpoints

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

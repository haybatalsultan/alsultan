# Automatic public item code

Each product receives an immutable, server-generated public item code after its database row is created.

Example:

`HS00001`

The code is derived from the database-generated primary key. This avoids `MAX()+1` race conditions during concurrent product creation. Browser-supplied SKU values are ignored, the database field remains unique/indexed, and existing codes cannot be edited through model saves.

`product_reference` (`HSP-...`) remains a separate immutable internal tracking reference.

Migration `0010_public_hs_sku` converts existing product SKUs to the same `HS` format deterministically. Historical order-item snapshots are intentionally not rewritten.

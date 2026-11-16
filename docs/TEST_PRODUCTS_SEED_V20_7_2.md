# v20.7.2 — Demo Product Seed

This utility is for **local pre-Render testing only**. It adds no models, fields, or migrations.

## What it creates

- 50 demo products using only the existing `Product` fields.
- Existing master-data models only: one Misbah category plus Amber, Mammoth Ivory, Elephant Ivory (test-only), and Yusr materials.
- Server-generated `product_reference` and `sku`; the command never supplies either field.
- Optional 3 clearly marked TEST images per product (150 total) through the existing Cloudinary upload/validation service.
- Elephant ivory records are explicitly marked test-only and use `verification_status=NONE`.

## Safe/idempotent behavior

The command identifies its own records by the `[TEST DATA]` marker and product name. Re-running updates those demo records instead of intentionally creating another set. Existing non-demo products are not selected for update.

It does not delete products or images.

## Run locally

Products only:

```bash
python manage.py seed_demo_products
```

Products + 3 Cloudinary images each:

```bash
python manage.py seed_demo_products --with-images
```

The image option requires valid `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` settings. Generated images are obvious placeholders and contain `TEST PRODUCT IMAGE` / `NOT A REAL PRODUCT PHOTO` so they cannot be confused with genuine stock photography.

## Important

Do not run this command in production. It is intended for local validation before Render deployment.

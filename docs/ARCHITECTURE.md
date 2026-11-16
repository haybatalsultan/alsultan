# Architecture
Cloudflare/domain → HTTPS → Render/Gunicorn → Django → PostgreSQL. Cloudinary serves permanent media. Redis is optional initially but recommended in production for distributed rate limiting/cache. Four apps are retained: accounts, catalog, orders, core. Business-critical operations live in service modules.

Owner-only financial truth is intentionally separated from operational product forms. Supervisors receive explicit boolean permissions and cannot access pricing service/forms unless future owner-authorized design changes this policy.

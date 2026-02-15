# SMS (System-School-Management) - Deployment Changes

All changes made to get the application running in production on `sms.jhpetitfrere.com`.

---

## 1. docker-compose-prod.yml

### nginx service
- **Removed** SSL volume mount (`./docker/production/ssl:/etc/nginx/ssl:ro`) since SSL is terminated by the host reverse proxy (Cloudflare -> host nginx -> Docker nginx on port 8081).
- **Changed ports** from `"80:80"` and `"443:443"` to `"8081:80"` to avoid port conflicts on the host.

### web service
- **Added** `env_file: - .env` before the environment block so the container can read variables from the `.env` file.
- **Added** `DJANGO_ENV=production` to the environment variables -- without this, `settings/__init__.py` defaults to development settings.
- **Replaced** `DATABASE_URL=postgresql://...` with individual database variables:
  - `DB_NAME=${DB_NAME:-school_management}`
  - `DB_USER=${DB_USER:-school_admin}`
  - `DB_PASSWORD=${DB_PASSWORD}`
  - `DB_HOST=db`
  - `DB_PORT=5432`
- **Replaced** `REDIS_URL=redis://...` with:
  - `REDIS_HOST=redis`
  - `REDIS_PASSWORD=${REDIS_PASSWORD}`
- **Added** `CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}` to environment variables.

### celery service
- **Added** `env_file: - .env`.
- **Added** `DJANGO_ENV=production`.
- **Replaced** `DATABASE_URL` with individual `DB_*` variables (same as web).
- **Replaced** `REDIS_URL` with `REDIS_HOST=redis` and `REDIS_PASSWORD=${REDIS_PASSWORD}`.

### celery-beat service
- Same changes as celery service.

### flower service
- Same changes as celery service.

---

## 2. School_System/settings/production.py

- **Added** `CSRF_TRUSTED_ORIGINS` configuration after `ALLOWED_HOSTS`, reading from the environment variable with a default of `https://sms.jhpetitfrere.com`.
- **Sentry import** was already wrapped in `try/except` with `SENTRY_AVAILABLE` flag (no change needed).
- **Replaced** the strict CSP block with a relaxed version:
  - `script-src` now allows `'unsafe-inline'`, `'unsafe-eval'`, and CDN domains (`cdn.jsdelivr.net`, `cdn.datatables.net`, `cdnjs.cloudflare.com`).
  - `style-src` now allows `'unsafe-inline'`, CDN domains, and `fonts.googleapis.com`.
  - `font-src` now allows Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`) and CDN domains.
- **Removed** the `report-uri` directive and the code that conditionally deleted it.
- **Added** `STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'` after the CSP block -- the manifest version fails on missing source map files (e.g., `pdfmake.min.js.map`).
- **Logging formatter** was already using the standard `%(asctime)s %(name)s %(levelname)s %(message)s` format (no change needed).

---

## 3. docker/production/nginx.conf

**Replaced the entire file** with an HTTP-only configuration:
- **Removed** the HTTP-to-HTTPS redirect server block.
- **Removed** the HTTPS/443/SSL server block entirely (no `ssl_certificate`, `ssl_protocols`, etc.).
- **Single server** block listening on port 80.
- **Changed** `X-Forwarded-Proto` from `$scheme` to `$http_x_forwarded_proto` in all proxy locations so the actual client protocol is correctly forwarded through the proxy chain, preventing infinite redirect loops when `SECURE_SSL_REDIRECT=True`.
- **Kept** all security headers, rate limiting zones, static/media file locations, and deny rules for sensitive files.

---

## 4. docker/production/docker-entrypoint-prod.sh

- **Replaced** `python manage.py migrate --noinput` with tenant-aware migration commands:
  ```bash
  python manage.py migrate_schemas --shared --noinput
  python manage.py migrate_schemas --tenant --noinput
  ```
- Both commands use `|| echo "[WARN] ..."` to make migration errors non-fatal on restart or when no tenants exist yet.

---

## 5. School_System/settings/base.py

- **Moved** `import_export` from `SHARED_APPS` to `TENANT_APPS` since it operates on tenant-specific data.
- The following apps were already correctly placed in `TENANT_APPS` (no changes needed):
  - `django.contrib.admin`
  - `allauth`, `allauth.account`, `allauth.socialaccount`, `allauth.mfa`
  - `django_otp`, `django_otp.plugins.otp_totp`, `django_otp.plugins.otp_static`
  - `rest_framework.authtoken`
  - `axes`
- `STATICFILES_STORAGE` was already set to `CompressedStaticFilesStorage` (no change needed).
- `CSRF_TRUSTED_ORIGINS` was already configured (no change needed).

---

## 6. requirements.txt

- `django-storages`, `stripe`, and `braintree` were already uncommented (no changes needed).

---

## 7. School_System/urls.py

- `debug_toolbar` URL inclusion was already wrapped in `if settings.DEBUG:` (no change needed).

---

## Summary

These changes prepare the application for deployment behind a host-level reverse proxy (e.g., Nginx, Caddy, or a cloud load balancer) that handles SSL termination. The key architectural decisions are:

1. **No SSL at the Docker level** -- SSL is handled by the host reverse proxy, so nginx inside Docker only serves HTTP on port 80.
2. **Port 8081** -- The Docker nginx exposes on port 8081 to avoid conflicts with the host reverse proxy on port 80/443.
3. **Individual DB variables** -- Instead of a single `DATABASE_URL`, individual `DB_*` variables are used for compatibility with `django-tenants` and `python-decouple`.
4. **Tenant-aware migrations** -- Uses `migrate_schemas` instead of `migrate` for proper multi-tenant schema management.
5. **Relaxed CSP** -- Allows CDN assets and inline styles/scripts needed by the frontend templates.
6. **X-Forwarded-Proto passthrough** -- Uses `$http_x_forwarded_proto` so Django correctly detects HTTPS even though the internal connection is HTTP.

---

## .env (not committed -- created on server)

- Created production environment file with all required variables: DB credentials, Redis password, Django secret key, allowed hosts, CSRF trusted origins, email config, Celery broker/result URLs, Flower credentials.

## Manual Steps (not in code)

- Created public tenant (schema_name='public') via Django shell.
- Created main school tenant (schema_name='sms_main', name='SMS School') with domain `sms.jhpetitfrere.com`.
- This triggered tenant schema creation and ran all tenant migrations.

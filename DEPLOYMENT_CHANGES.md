# SMS (System-School-Management) - Deployment Changes

All changes made to get the application running in production on `sms.jhpetitfrere.com`.

---

## docker-compose-prod.yml
- Changed nginx ports from `80:80` / `443:443` to `8081:80` to avoid conflict with host nginx (Cloudflare -> host nginx -> Docker nginx)
- Removed SSL volume mount (`./docker/production/ssl:/etc/nginx/ssl:ro`) — SSL is terminated at Cloudflare/host nginx level
- Added `env_file: .env` to web, celery, celery-beat, flower services
- Changed environment from single `DATABASE_URL` to individual `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` variables (matching what `decouple.config()` expects in settings)
- Added `DJANGO_ENV=production` to all app services (web, celery, celery-beat, flower) — without this, `settings/__init__.py` defaults to development settings
- Added `CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}` to web service
- Added `REDIS_HOST=redis` to all services

## .env
- Created production environment file with all required variables: DB credentials, Redis password, Django secret key, allowed hosts, CSRF trusted origins, email config, Celery broker/result URLs, Flower credentials

## School_System/settings/production.py
- Made `sentry_sdk` import conditional with `try/except` and `HAS_SENTRY` flag — sentry-sdk is not installed
- Replaced `pythonjsonlogger.JsonFormatter` with standard Python log formatter — pythonjsonlogger is not installed
- Added `CSRF_TRUSTED_ORIGINS` read from environment variable
- Changed `STATICFILES_STORAGE` from `CompressedManifestStaticFilesStorage` to `CompressedStaticFilesStorage` — the manifest version fails on missing source map files (e.g., `pdfmake.min.js.map`)
- Relaxed Content Security Policy to allow:
  - `'unsafe-inline'` and `'unsafe-eval'` for scripts (needed by vendor JS libraries and inline `<script>` blocks in templates)
  - `'unsafe-inline'` for styles (needed by inline `style=` attributes throughout templates)
  - CDN domains: `cdn.jsdelivr.net`, `cdn.datatables.net`, `cdnjs.cloudflare.com` (used by DataTables and other vendor libs)
  - Google Fonts: `fonts.googleapis.com` (style-src), `fonts.gstatic.com` (font-src) — loaded via `@import` in `style.css`
- Added `USE_X_FORWARDED_HOST = True` and `USE_X_FORWARDED_PORT = True` for nginx proxy chain

## School_System/settings/base.py
- Reorganized `SHARED_APPS` and `TENANT_APPS` for django-tenants compatibility:
  - Moved to `TENANT_APPS`: `django.contrib.admin`, `allauth`, `allauth.account`, `allauth.socialaccount`, `allauth.mfa`, `django_otp`, `django_otp.plugins.otp_totp`, `django_otp.plugins.otp_static`, `rest_framework.authtoken`, `axes`, `import_export`
  - These apps reference `AUTH_USER_MODEL` (accounts.User) which lives in the tenant schema, so they must be tenant apps

## School_System/urls.py
- Wrapped `debug_toolbar` URL inclusion in `if settings.DEBUG:` — in production, debug_toolbar is installed but not in `INSTALLED_APPS`, causing `RuntimeError: Model class debug_toolbar.models.HistoryEntry doesn't declare an explicit app_label`

## requirements.txt
- Uncommented/added: `django-storages==1.14.6`, `stripe==14.0.1`, `braintree==4.29.0` — these were commented out but imported by app code (payments/views_frontend.py)

## core/migrations/0002_add_tenant_fields.py (NEW)
- Added migration to create fields required by django-tenants:
  - `AddField`: `school.schema_name` (CharField, max_length=63, unique, db_index)
  - `RenameField`: `domain.school` -> `domain.tenant` (DomainMixin convention)
  - `AlterModelOptions`: Updated School verbose names to indicate tenant role

## custom_context_processor.py (NEW)
- Created context processor providing the `dz_array` template variable required by the w3crm theme
- `dz_array.public`: title, description, favicon path
- `dz_array.global.css`: Bootstrap, animate, perfect-scrollbar, metismenu, deznav, style.css
- `dz_array.global.js.top`: global.min.js (jQuery + core bundled libs)
- `dz_array.global.js.bottom`: Bootstrap bundle, perfect-scrollbar, metismenu, deznav, deznav-init, custom.min.js
- Without this, ALL templates render without any CSS or JavaScript

## docker/production/docker-entrypoint-prod.sh
- Changed from single `python manage.py migrate --noinput` to separate shared/tenant migration commands:
  - `python manage.py migrate_schemas --shared --noinput`
  - `python manage.py migrate_schemas --tenant --noinput`
- Added `|| echo "[WARN]..."` to make migration errors non-fatal on restart

## docker/production/nginx.conf
- Changed SSL redirect check from `$scheme` to `$http_x_forwarded_proto` to prevent infinite redirect loops when behind Cloudflare/host nginx that terminates SSL

## Manual Steps (not in code)
- Created public tenant (schema_name='public') via Django shell
- Created main school tenant (schema_name='sms_main', name='SMS School') with domain `sms.jhpetitfrere.com`
- This triggered tenant schema creation and ran all tenant migrations

# Security Documentation

This document outlines the security architecture, best practices, threat model, and security guidelines for the School Management System.

## Table of Contents

- [Security Architecture](#security-architecture)
- [Authentication & Authorization](#authentication--authorization)
- [Data Protection](#data-protection)
- [Network Security](#network-security)
- [Application Security](#application-security)
- [Tenant Isolation](#tenant-isolation)
- [API Security](#api-security)
- [Threat Model](#threat-model)
- [Security Best Practices](#security-best-practices)
- [Incident Response](#incident-response)
- [Security Checklist](#security-checklist)
- [Reporting Vulnerabilities](#reporting-vulnerabilities)

## Security Architecture

### Defense in Depth

The system implements multiple layers of security:

```
┌─────────────────────────────────────────┐
│        Layer 1: Network Security         │
│   Firewall, DDoS Protection, WAF        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│       Layer 2: Transport Security        │
│         TLS 1.2+, HSTS, SSL             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Layer 3: Application Security       │
│   Authentication, Authorization, CSRF    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Layer 4: Data Security           │
│  Encryption, Tenant Isolation, Backup    │
└─────────────────────────────────────────┘
```

### Security Principles

1. **Least Privilege** - Users have minimum permissions needed
2. **Defense in Depth** - Multiple security layers
3. **Fail Secure** - System fails to secure state
4. **Complete Mediation** - Every access is checked
5. **Separation of Duties** - Critical operations require multiple approvals
6. **Open Design** - Security through design, not obscurity

## Authentication & Authorization

### Two-Factor Authentication (2FA)

**Required for:**
- All staff members
- Professors
- Direction members
- System administrators

**Implementation:**
- django-allauth MFA
- TOTP-based (Time-based One-Time Password)
- Backup codes for account recovery
- QR code for easy setup

**Configuration:**
```python
# settings.py
ALLAUTH_2FA_FORCE_2FA = True
TWO_FACTOR_MANDATORY = True
```

### Password Security

**Requirements:**
- Minimum 8 characters
- Must contain uppercase, lowercase, numbers
- Cannot be commonly used passwords
- Cannot be similar to username/email
- Password history (last 5 passwords)
- Expires every 90 days (configurable)

**Storage:**
- Argon2 password hashing (memory-hard)
- Salt per password
- Configurable work factor

**Configuration:**
```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
```

### Session Management

**Security measures:**
- Session timeout: 14 days (configurable)
- Secure cookie flags (httpOnly, secure, sameSite)
- Session invalidation on password change
- Concurrent session limits
- Redis-backed sessions for performance

**Configuration:**
```python
SESSION_COOKIE_AGE = 1209600  # 14 days
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True
```

### OAuth Social Login

**Supported providers:**
- Google
- GitHub
- Facebook
- LinkedIn

**Security:**
- OAuth 2.0 protocol
- State parameter for CSRF protection
- Email verification required
- 2FA enforcement after OAuth login

### Login Protection

**django-axes Configuration:**
- Maximum 5 failed login attempts
- 1-hour lockout after max attempts
- IP-based and username-based tracking
- Whitelist for admin IPs
- Email notification on lockout

**Configuration:**
```python
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
AXES_NEVER_LOCKOUT_WHITELIST = ['127.0.0.1']
```

### Role-Based Access Control (RBAC)

**Roles:**

1. **Student**
   - View own courses, grades, attendance
   - Download own report cards
   - Access course materials

2. **Parent**
   - View linked student's data only
   - Receive notifications
   - No modification rights

3. **Professor**
   - Manage own courses
   - Record attendance for own classes
   - Grade own students
   - Upload course materials

4. **Direction**
   - All professor permissions
   - Create/manage users
   - Global search
   - View all data
   - Manage payments

5. **Admin**
   - Full system access
   - Manage tenants
   - System configuration
   - Access all tenant data

**Permission Checking:**
```python
# Decorators
@login_required
@role_required('professor')
def view_function(request):
    pass

# Template checks
{% if user.is_lecturer %}
  <!-- Professor content -->
{% endif %}

# Programmatic checks
if request.user.has_perm('course.add_course'):
    # Allow course creation
```

## Data Protection

### Encryption

**Data in Transit:**
- TLS 1.2+ for all connections
- HSTS with preload
- Strict cipher suites
- Perfect Forward Secrecy (PFS)

**Data at Rest:**
- Database: PostgreSQL transparent data encryption (TDE)
- Backups: AES-256 encryption
- Media files: Encrypted S3 buckets
- Sensitive fields: Field-level encryption

### PII Protection

**Personal Identifiable Information:**
- Student names, addresses, phone numbers
- Parent contact information
- Financial information
- Academic records

**Protection measures:**
- Access logging for PII access
- Encryption at rest
- Minimization - collect only necessary data
- Retention policies
- Secure deletion procedures

### Data Minimization

**Logging:**
- Never log passwords or tokens
- Redact sensitive data in logs
- PII pseudonymization in logs

**Example:**
```python
# Bad
logger.info(f"User {user.email} logged in with password {password}")

# Good
logger.info(f"User {user.id} logged in successfully")
```

### Backup Security

**Backup strategy:**
- Daily automated backups
- Encrypted backups (AES-256)
- Off-site storage (S3)
- 30-day retention
- Tested restore procedures

**Access control:**
- Backup encryption keys in secure vault
- Restricted access to backups
- Audit log for backup access

## Network Security

### Firewall Configuration

**UFW Rules:**
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### DDoS Protection

**Measures:**
- Rate limiting per IP
- Connection limits
- Cloudflare or similar CDN
- nginx rate limiting zones
- Request size limits

**nginx configuration:**
```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_conn_zone $binary_remote_addr zone=addr:10m;

limit_conn addr 10;
client_max_body_size 100M;
```

### SSL/TLS Configuration

**Best practices:**
- Use Let's Encrypt or valid CA
- TLS 1.2 and 1.3 only
- Strong cipher suites
- OCSP stapling
- Certificate pinning (optional)

**nginx SSL config:**
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
```

### Database Security

**PostgreSQL hardening:**
- Bind to localhost only
- Strong passwords
- SSL connections required
- Role-based access
- Connection limits
- Query logging

**pg_hba.conf:**
```
local   all   postgres   peer
local   all   all        md5
host    all   all   127.0.0.1/32   md5
hostssl all   all   0.0.0.0/0      md5
```

### Redis Security

**Configuration:**
```conf
bind 127.0.0.1
requirepass <strong-password>
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## Application Security

### CSRF Protection

**Django CSRF:**
- Enabled by default
- CSRF tokens on all forms
- SameSite cookies
- Referer validation

**Configuration:**
```python
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True
```

### XSS Protection

**Measures:**
- Auto-escaping in templates
- Content Security Policy (CSP)
- X-XSS-Protection header
- Input validation
- Output encoding
- Use of `bleach` for rich text

**CSP Configuration:**
```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'",)
```

### SQL Injection Prevention

**Measures:**
- Django ORM (parameterized queries)
- No raw SQL without parameterization
- Input validation
- Least privilege database users

**Safe practices:**
```python
# Safe - ORM
User.objects.filter(username=username)

# Safe - Parameterized
User.objects.raw('SELECT * FROM users WHERE username = %s', [username])

# NEVER - String concatenation
User.objects.raw(f'SELECT * FROM users WHERE username = {username}')  # ❌
```

### File Upload Security

**Validation:**
- File type validation
- File size limits
- Virus scanning (optional)
- Rename files
- Store outside web root
- Serve via signed URLs

**Configuration:**
```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
ALLOWED_UPLOAD_EXTENSIONS = ['pdf', 'docx', 'jpg', 'png']

# Validate file extension
allowed_extensions = validator.FileExtensionValidator(['pdf', 'docx'])
```

### Command Injection Prevention

**Measures:**
- Avoid subprocess calls
- Use libraries instead of shell commands
- Validate all inputs
- Whitelist approach

**Safe practices:**
```python
# Bad - Shell injection risk
import os
os.system(f'convert {user_file} output.pdf')

# Good - Use library
from pdf_converter import convert
convert(user_file, 'output.pdf')
```

### Security Headers

**Django configuration:**
```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## Tenant Isolation

### Schema-Level Isolation

**Implementation:**
- PostgreSQL schema per tenant
- django-tenants middleware
- Automatic tenant routing by domain
- No cross-tenant queries

**How it works:**
```
Request: school1.example.com
↓
Middleware identifies tenant
↓
Sets PostgreSQL schema: school_school1
↓
All queries scoped to that schema
↓
No access to other schemas
```

### Tenant Security

**Measures:**
- License validation per tenant
- Subscription expiry checks
- Tenant-specific rate limits
- Isolated backups per tenant
- Separate encryption keys (optional)

**Middleware check:**
```python
def process_request(self, request):
    tenant = get_tenant(request)
    if not tenant.is_subscription_valid():
        return HttpResponse('Subscription expired', status=403)
```

### Cross-Tenant Prevention

**Checks:**
- Tenant filter on all queries
- No tenant ID in URLs
- Domain-based routing only
- Audit logs for all access

## API Security

### Authentication

**JWT Token:**
- Short-lived access tokens (50 minutes)
- Long-lived refresh tokens (10 days)
- Token rotation
- Blacklist on logout

**Configuration:**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=50),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=10),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### Rate Limiting

**DRF Throttling:**
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

### Input Validation

**Serializer validation:**
```python
class StudentSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[validate_email])
    phone = serializers.RegexField(regex=r'^\+?1?\d{9,15}$')

    def validate_age(self, value):
        if value < 5 or value > 100:
            raise serializers.ValidationError("Invalid age")
        return value
```

### CORS Configuration

**Production:**
```python
CORS_ALLOWED_ORIGINS = [
    "https://example.com",
    "https://www.example.com",
]
CORS_ALLOW_CREDENTIALS = True
```

## Threat Model

### Threat Actors

1. **External Attackers**
   - Script kiddies
   - Professional hackers
   - Competitors
   - Nation-state actors (low probability)

2. **Internal Threats**
   - Disgruntled employees
   - Negligent users
   - Compromised accounts

3. **Automated Threats**
   - Bots
   - Scrapers
   - DDoS attacks

### Attack Vectors

#### 1. Authentication Bypass
**Threat:** Attacker gains unauthorized access
**Mitigations:**
- 2FA mandatory for staff
- Strong password policy
- Account lockout after failed attempts
- Session timeout
- Secure password reset flow

#### 2. Privilege Escalation
**Threat:** User gains higher privileges
**Mitigations:**
- RBAC strictly enforced
- Permission checks on all operations
- Audit logging
- Separation of duties

#### 3. Data Breach
**Threat:** Unauthorized access to sensitive data
**Mitigations:**
- Tenant isolation at schema level
- Encryption at rest and in transit
- Access logging
- Minimum data collection
- Secure deletion

#### 4. SQL Injection
**Threat:** Database manipulation
**Mitigations:**
- Django ORM
- Parameterized queries
- Input validation
- Least privilege DB users

#### 5. XSS (Cross-Site Scripting)
**Threat:** Inject malicious scripts
**Mitigations:**
- Auto-escaping templates
- CSP headers
- Input validation
- Output encoding

#### 6. CSRF (Cross-Site Request Forgery)
**Threat:** Unauthorized actions
**Mitigations:**
- CSRF tokens
- SameSite cookies
- Referer validation
- Double-submit cookies

#### 7. DDoS
**Threat:** Service unavailability
**Mitigations:**
- Rate limiting
- CDN (Cloudflare)
- Connection limits
- Auto-scaling

#### 8. Social Engineering
**Threat:** Trick users into revealing credentials
**Mitigations:**
- User security training
- 2FA
- Email verification
- Suspicious login detection

## Security Best Practices

### For Developers

1. **Never commit secrets**
   - Use `.env` files
   - Add `.env` to `.gitignore`
   - Use environment variables

2. **Validate all inputs**
   - Server-side validation
   - Whitelist, not blacklist
   - Sanitize and escape

3. **Keep dependencies updated**
   - Regular `pip` updates
   - Monitor security advisories
   - Use `safety check`

4. **Code reviews**
   - All code reviewed
   - Security checklist
   - Automated scanning

5. **Logging**
   - Log security events
   - Never log secrets
   - Monitor logs regularly

### For Administrators

1. **Strong passwords**
   - Minimum 16 characters
   - Use password manager
   - Unique per service

2. **Regular updates**
   - OS patches
   - Application updates
   - Security updates immediately

3. **Backup verification**
   - Test restores monthly
   - Verify backup integrity
   - Encrypted backups

4. **Monitoring**
   - Set up alerts
   - Monitor failed logins
   - Track unusual activity

5. **Least privilege**
   - Minimum necessary access
   - Regular access reviews
   - Remove unused accounts

### For Users

1. **Strong passwords**
   - Unique password
   - Use password manager
   - Never share passwords

2. **Enable 2FA**
   - Use authenticator app
   - Save backup codes
   - Don't share codes

3. **Verify emails**
   - Check sender
   - Don't click suspicious links
   - Report phishing

4. **Log out**
   - Log out when done
   - Don't save passwords on shared devices
   - Clear browser data

## Incident Response

### Preparation

1. **Response team**
   - Designated incident response team
   - Contact information
   - Escalation procedures

2. **Tools**
   - Monitoring tools
   - Forensic tools
   - Communication channels

3. **Procedures**
   - Incident response plan
   - Regular drills
   - Post-mortem template

### Detection

**Indicators of compromise:**
- Unusual login patterns
- Multiple failed login attempts
- Unexpected data access
- Performance degradation
- Error spikes
- Suspicious network traffic

### Response Steps

1. **Identification**
   - Confirm incident
   - Determine scope
   - Document everything

2. **Containment**
   - Isolate affected systems
   - Disable compromised accounts
   - Block malicious IPs
   - Preserve evidence

3. **Eradication**
   - Remove malware
   - Patch vulnerabilities
   - Reset credentials
   - Update firewall rules

4. **Recovery**
   - Restore from backups
   - Verify system integrity
   - Monitor for recurrence
   - Gradual service restoration

5. **Lessons Learned**
   - Post-incident review
   - Update procedures
   - Implement improvements
   - Train team

### Communication

**Internal:**
- Notify incident response team
- Update management
- Inform affected users

**External:**
- Notify authorities if required
- Communicate with affected parties
- Public disclosure (if necessary)

## Security Checklist

### Development
- [ ] No hardcoded credentials
- [ ] All inputs validated
- [ ] SQL injection prevented
- [ ] XSS protection enabled
- [ ] CSRF protection enabled
- [ ] Dependencies up to date
- [ ] Security headers configured
- [ ] Logging implemented
- [ ] Error handling secure

### Deployment
- [ ] DEBUG=False
- [ ] Strong SECRET_KEY
- [ ] HTTPS enforced
- [ ] Secure cookies
- [ ] Firewall configured
- [ ] Database secured
- [ ] Redis password set
- [ ] Backups automated
- [ ] Monitoring enabled

### Operations
- [ ] Regular updates
- [ ] Backup testing
- [ ] Log monitoring
- [ ] Access reviews
- [ ] Vulnerability scanning
- [ ] Incident drills
- [ ] Security training
- [ ] Compliance audits

## Reporting Vulnerabilities

### Responsible Disclosure

If you discover a security vulnerability:

1. **Do NOT:**
   - Exploit the vulnerability
   - Share with others
   - Disclose publicly

2. **Do:**
   - Email: security@rhematek-solutions.com
   - Include detailed description
   - Provide steps to reproduce
   - Suggest fix if possible

3. **Response timeline:**
   - Initial response: 24 hours
   - Fix for critical: 7 days
   - Fix for high: 30 days
   - Public disclosure: 90 days (coordinated)

### Bug Bounty

- Rewards for valid vulnerabilities
- Based on severity and impact
- Coordinated disclosure required

### Hall of Fame

Contributors who responsibly disclose vulnerabilities will be credited (with permission).

---

**Security Contact:** security@rhematek-solutions.com
**Last Updated:** December 24, 2025
**Next Review:** March 24, 2026

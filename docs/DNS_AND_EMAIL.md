# DNS and Email Configuration

This document defines the exact DNS records and email authentication setup required for Nexo production.

## Domain Structure

| Domain | Purpose | Provider |
|--------|---------|----------|
| `nexo.example` | Apex domain (redirect to app) | External DNS |
| `app.nexo.example` | Web application (Vercel) | Vercel |
| `api.nexo.example` | API (Railway) | Railway |
| `staging.nexo.example` | Staging web (Vercel Preview) | Vercel |
| `api-staging.nexo.example` | Staging API (Railway) | Railway |

## DNS Records

### Production

| Name | Type | Value | TTL | Notes |
|------|------|-------|-----|-------|
| `@` | A | `76.76.21.21` | 3600 | Vercel IP (verify current) |
| `@` | AAAA | `2606:4700::6810:xxxx` | 3600 | Vercel IPv6 |
| `app` | CNAME | `cname.vercel-dns.com` | 3600 | Vercel custom domain |
| `api` | CNAME | `nexo-api-production.up.railway.app` | 3600 | Railway custom domain |
| `_dmarc` | TXT | `v=DMARC1; p=none; rua=mailto:dmarc@nexo.example` | 3600 | Start with monitoring |
| `nexo.example` | TXT | `v=spf1 include:_spf.resend.com ~all` | 3600 | SPF for Resend |
| `default._domainkey` | CNAME | `default._domainkey.resend.com` | 3600 | DKIM selector 1 |
| `default2._domainkey` | CNAME | `default2._domainkey.resend.com` | 3600 | DKIM selector 2 |

### Staging

| Name | Type | Value | TTL | Notes |
|------|------|-------|-----|-------|
| `staging` | CNAME | `cname.vercel-dns.com` | 3600 | Vercel preview |
| `api-staging` | CNAME | `nexo-api-staging.up.railway.app` | 3600 | Railway staging |
| `_dmarc.staging` | TXT | `v=DMARC1; p=none; rua=mailto:dmarc@nexo.example` | 3600 | |
| `staging.nexo.example` | TXT | `v=spf1 include:_spf.resend.com ~all` | 3600 | |
| `default._domainkey.staging` | CNAME | `default._domainkey.resend.com` | 3600 | |
| `default2._domainkey.staging` | CNAME | `default2._domainkey.resend.com` | 3600 | |

## Email Authentication (Resend)

### Setup Order

1. **Add domain in Resend dashboard**
   - Domain: `nexo.example` (production)
   - Domain: `staging.nexo.example` (staging)

2. **Configure DNS records** (from Resend dashboard)
   - SPF (TXT)
   - DKIM (2x CNAME)
   - DMARC (TXT) - start with `p=none`

3. **Verify domain in Resend**
   - Wait for DNS propagation (up to 48h)
   - Click "Verify" in Resend

4. **Align sender address**
   - From: `Nexo <no-reply@nexo.example>`
   - Must match verified domain

5. **DMARC progression**
   - Week 1-2: `p=none` (monitoring)
   - Week 3-4: `p=quarantine` (review reports)
   - Week 5+: `p=reject` (enforcement)

### DMARC Record Details

```txt
# Monitoring phase
v=DMARC1; p=none; rua=mailto:dmarc@nexo.example; ruf=mailto:dmarc-forensic@nexo.example; fo=1

# Enforcement phase (after review)
v=DMARC1; p=reject; rua=mailto:dmarc@nexo.example; ruf=mailto:dmarc-forensic@nexo.example; fo=1; sp=reject; adkim=s; aspf=s
```

### SPF Record Details

```txt
v=spf1 include:_spf.resend.com ~all
```

### DKIM Records

Resend provides two DKIM selectors. Add both as CNAME:

| Host | Type | Value |
|------|------|-------|
| `default._domainkey` | CNAME | `default._domainkey.resend.com` |
| `default2._domainkey` | CNAME | `default2._domainkey.resend.com` |

## Vercel Custom Domain Setup

1. In Vercel project settings → Domains
2. Add `app.nexo.example` (production)
3. Add `staging.nexo.example` (preview)
4. Vercel provides verification TXT record
5. Add to DNS, wait for Vercel verification
6. Enable "HTTPS Only" and "HSTS" in Vercel settings

## Railway Custom Domain Setup

1. In Railway project → Service → Settings → Domains
2. Add `api.nexo.example` (production)
3. Add `api-staging.nexo.example` (staging)
4. Railway provides CNAME target
5. Add to DNS
6. Railway auto-provisions TLS (Let's Encrypt)

## HTTPS Validation

After DNS propagation:

```bash
# Verify web
curl -I https://app.nexo.example
# Should return: 200 OK, HSTS, CSP headers

# Verify API
curl -I https://api.nexo.example/health
# Should return: 200 OK, JSON {"status":"ok"}

# Verify TLS
openssl s_client -connect app.nexo.example:443 -servername app.nexo.example < /dev/null
openssl s_client -connect api.nexo.example:443 -servername api.nexo.example < /dev/null
```

## Sender Alignment Checklist

- [ ] `From` header domain matches verified Resend domain
- [ ] `Return-Path` domain aligns with SPF domain
- [ ] DKIM signature domain aligns with `From` domain
- [ ] DMARC policy published and passing
- [ ] No personal mailbox credentials used (use `no-reply@`)

## Verification Commands

```bash
# Check all DNS records
dig +short app.nexo.example CNAME
dig +short api.nexo.example CNAME
dig +short _dmarc.nexo.example TXT
dig +short nexo.example TXT
dig +short default._domainkey.nexo.example CNAME

# Verify email delivery
# Send test via Resend dashboard or API
# Check inbox, spam, and DMARC reports
```

## Monitoring

- **DMARC reports**: Check `dmarc@nexo.example` weekly
- **Resend dashboard**: Monitor delivery rates, bounces, complaints
- **Vercel analytics**: Monitor web performance
- **Railway metrics**: Monitor API latency and errors
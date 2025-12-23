# SSL/TLS Certificates

## Required Files

Place your SSL/TLS certificate files in this directory:

- **server.crt** - Your SSL certificate (or certificate chain)
- **server.key** - Your private key

## File Names

The Nginx configuration expects these exact filenames:
```
certs/
├── server.crt
└── server.key
```

## Security

⚠️ **Important**:
- Keep your private key (`server.key`) secure
- Set appropriate permissions: `chmod 600 server.key`
- Never commit these files to version control
- The `.gitignore` file should already exclude `*.crt` and `*.key` files

## Certificate Formats

The certificates should be in PEM format (Base64 encoded).

### If you have a certificate chain:
Concatenate them in this order in `server.crt`:
1. Your server certificate
2. Intermediate certificate(s)
3. Root CA certificate (optional)

Example:
```bash
cat your-cert.crt intermediate.crt > server.crt
```

## Testing with Self-Signed Certificate (Development Only)

If you need to generate a self-signed certificate for testing:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key \
  -out server.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

⚠️ **Do not use self-signed certificates in production!**

## Verification

After placing your certificates, verify them:

```bash
# Check certificate
openssl x509 -in server.crt -text -noout

# Verify private key matches certificate
openssl x509 -noout -modulus -in server.crt | openssl md5
openssl rsa -noout -modulus -in server.key | openssl md5
# The MD5 hashes should match
```

## File Permissions

Recommended permissions:
```bash
chmod 644 server.crt
chmod 600 server.key
```

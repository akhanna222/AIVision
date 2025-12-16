# 🌐 Public UI Access on AWS EC2

Complete guide to exposing the Template Builder and Simple Extraction UIs publicly on AWS EC2.

---

## 📋 Overview

After deploying AIVision to EC2, you can access the public template builder and extraction UIs from anywhere without authentication. This guide shows you how to:

1. **Configure security groups** for public access
2. **Update CORS settings** to allow external API calls
3. **Access the public UIs** via browser
4. **Optionally setup a domain name** for professional URLs
5. **Secure your deployment** with SSL

---

## 🔓 What's Publicly Accessible?

### Without Authentication:
- **Template Builder UI** (`/template-builder`) - Create custom OCR templates
- **Simple Extraction UI** (`/simple-extract`) - Extract data using templates
- **Public API Endpoints**:
  - `POST /api/v1/public/templates` - Save templates
  - `POST /api/v1/public/extract/{template_name}` - Extract using template

### With Authentication (API Token):
- All other API endpoints (`/api/v1/extractions/*`)
- Account management
- Multi-model extraction

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Verify Deployment

Ensure you've deployed using the deployment script:

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Check services are running
sudo systemctl status aivision
sudo systemctl status nginx
```

Both should show **"active (running)"** in green.

### Step 2: Configure Security Group

Your EC2 security group must allow public HTTP/HTTPS access:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP | SSH access (restrict to your IP) |
| HTTP | TCP | 80 | 0.0.0.0/0 | Public web access |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Secure public access |

**To configure:**

1. Go to AWS EC2 Console → Instances
2. Select your instance → Security → Security groups
3. Click the security group link
4. Edit inbound rules
5. Add rules as shown above
6. Save rules

### Step 3: Update CORS Configuration

The backend needs to allow requests from any origin for public UIs:

```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Edit environment file
sudo nano /opt/aivision/.env
```

Update the CORS settings:

```bash
# Change this line:
ALLOWED_ORIGINS=http://localhost,https://yourdomain.com

# To this (allow all origins for public API):
ALLOWED_ORIGINS=*
```

Or for more security, allow specific origins:

```bash
ALLOWED_ORIGINS=http://your-ec2-ip,https://yourdomain.com,http://localhost:3000
```

Restart the backend:

```bash
sudo systemctl restart aivision
```

### Step 4: Access Public UIs

Get your EC2 public IP:

```bash
# On your local machine
aws ec2 describe-instances --instance-ids i-YOUR_INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress'

# Or from EC2 instance
curl ifconfig.me
```

Access the UIs in your browser:

```
Template Builder:
http://YOUR_EC2_PUBLIC_IP/template-builder

Simple Extraction:
http://YOUR_EC2_PUBLIC_IP/simple-extract
```

---

## 🌍 Setup Custom Domain (Optional, 10 minutes)

For professional URLs like `https://ocr.yourdomain.com`:

### Step 1: Point Domain to EC2

1. Get your EC2 **Elastic IP** (recommended for static IP):
   ```bash
   # Allocate Elastic IP in AWS Console
   # Associate it with your EC2 instance
   ```

2. Update DNS records (in your domain registrar):
   ```
   Type: A Record
   Name: ocr (or @ for root domain)
   Value: YOUR_ELASTIC_IP
   TTL: 300
   ```

3. Wait 5-10 minutes for DNS propagation

### Step 2: Update Nginx Configuration

```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Edit Nginx config
sudo nano /etc/nginx/sites-available/aivision
```

Update the `server_name`:

```nginx
server {
    listen 80;
    server_name ocr.yourdomain.com;  # Change this line

    # ... rest of config
}
```

Test and restart Nginx:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### Step 3: Setup SSL Certificate

```bash
# Install Let's Encrypt certificate
sudo certbot --nginx -d ocr.yourdomain.com

# Follow prompts:
# - Enter email: your@email.com
# - Agree to terms: Y
# - Share email: N
# - Redirect HTTP to HTTPS: 2 (recommended)
```

Certificate will auto-renew every 90 days.

### Step 4: Access via Domain

```
Template Builder:
https://ocr.yourdomain.com/template-builder

Simple Extraction:
https://ocr.yourdomain.com/simple-extract
```

---

## 🔒 Security Best Practices

### 1. Use HTTPS (SSL)

Always use SSL certificates for public deployments:

```bash
# Install SSL certificate
sudo certbot --nginx -d ocr.yourdomain.com
```

### 2. Rate Limiting

Nginx is already configured with rate limiting. To adjust:

```bash
sudo nano /etc/nginx/sites-available/aivision
```

Add before the `server` block:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=2r/s;

server {
    # ... existing config

    # Apply rate limits
    location /api/v1/public {
        limit_req zone=api_limit burst=20 nodelay;
        # ... rest of location config
    }
}
```

Restart Nginx:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 3. File Upload Limits

Already configured to 50MB max. To change:

```bash
sudo nano /etc/nginx/sites-available/aivision
```

```nginx
server {
    # Change this value
    client_max_body_size 50M;  # Adjust as needed
}
```

### 4. IP Whitelisting (Optional)

Restrict access to specific IPs:

```nginx
server {
    # Allow specific IPs
    allow 203.0.113.0/24;  # Your office network
    allow 198.51.100.5;    # Your home IP
    deny all;

    # ... rest of config
}
```

### 5. Add API Key for Public Endpoints (Recommended)

While the public endpoints don't require authentication, you can add optional API keys for tracking:

Edit `.env`:

```bash
PUBLIC_API_KEYS=key1:description1,key2:description2
```

This allows you to track usage per key while keeping endpoints publicly accessible.

---

## 📱 Using Public UIs

### Template Builder

1. **Open browser**: `http://YOUR_EC2_IP/template-builder`
2. **Choose a preset** or create custom template:
   - Click "Mortgage Documents" for pre-built template
   - OR add custom fields manually
3. **Save template**:
   - Enter template name (e.g., "my_invoice")
   - Click "Save Template & Get API Endpoint"
4. **Copy API endpoint**:
   ```
   POST http://YOUR_EC2_IP/api/v1/public/extract/my_invoice
   ```

### Simple Extraction

1. **Open browser**: `http://YOUR_EC2_IP/simple-extract`
2. **Select template**: Choose from dropdown
3. **Upload document**: Drag & drop or click to upload
4. **Configure options** (optional):
   - Enable multi-model extraction
   - Choose models and strategy
5. **Extract**: Click "Extract Document"
6. **View results**: See extracted fields with confidence scores

---

## 🧪 Testing Public Access

### From Your Local Machine

Test the public API endpoints:

```bash
# 1. Save a template
curl -X POST http://YOUR_EC2_IP/api/v1/public/templates \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "test_invoice",
    "fields": [
      {"name": "total_amount", "description": "Total amount due"},
      {"name": "invoice_number", "description": "Invoice number"}
    ]
  }'

# 2. Extract using the template
curl -X POST http://YOUR_EC2_IP/api/v1/public/extract/test_invoice \
  -F "file=@invoice.pdf" \
  -F "model=gemini-2.0-flash-exp"
```

### From Another Server

Test CORS is working:

```javascript
// JavaScript example
fetch('http://YOUR_EC2_IP/api/v1/public/templates', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    template_name: 'my_template',
    fields: [
      {name: 'field1', description: 'First field'}
    ]
  })
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

---

## 🔧 Troubleshooting

### Cannot Access UI from Browser

**Problem**: Browser shows "Connection timed out"

**Solutions**:

1. Check security group allows HTTP (port 80):
   ```bash
   # Verify in AWS Console → EC2 → Security Groups
   # Inbound rules should have: HTTP, TCP, 80, 0.0.0.0/0
   ```

2. Check Nginx is running:
   ```bash
   sudo systemctl status nginx
   # If not running:
   sudo systemctl start nginx
   ```

3. Check firewall:
   ```bash
   sudo ufw status
   # Should show: 80/tcp ALLOW Anywhere
   ```

### CORS Errors in Browser Console

**Problem**: "Access to fetch has been blocked by CORS policy"

**Solution**:

```bash
# SSH into EC2
sudo nano /opt/aivision/.env

# Update CORS:
ALLOWED_ORIGINS=*

# Restart backend
sudo systemctl restart aivision
```

### SSL Certificate Issues

**Problem**: "Your connection is not private"

**Solutions**:

1. Ensure domain DNS is correct:
   ```bash
   nslookup ocr.yourdomain.com
   # Should point to your EC2 IP
   ```

2. Reinstall certificate:
   ```bash
   sudo certbot --nginx -d ocr.yourdomain.com --force-renewal
   ```

3. Check Nginx SSL config:
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Upload Fails with Large Files

**Problem**: "413 Request Entity Too Large"

**Solution**:

```bash
# Increase upload limit
sudo nano /etc/nginx/sites-available/aivision

# Change:
client_max_body_size 100M;  # Increase to 100MB

# Restart Nginx
sudo systemctl restart nginx
```

### Template Not Found

**Problem**: "Template 'my_template' not found"

**Solution**:

1. Check template exists:
   ```bash
   curl http://YOUR_EC2_IP/api/v1/public/templates
   ```

2. Verify template name (case-sensitive):
   ```bash
   # Template names are lowercase and use underscores
   # ✓ Correct: my_invoice
   # ✗ Wrong: My Invoice, my-invoice
   ```

---

## 📊 Monitoring Public Access

### View Access Logs

```bash
# Nginx access logs (all requests)
sudo tail -f /var/log/nginx/aivision_access.log

# Filter for public API requests
sudo grep "/api/v1/public" /var/log/nginx/aivision_access.log

# Backend logs
sudo journalctl -u aivision -f

# Filter for template creation
sudo journalctl -u aivision | grep "template"
```

### Monitor Usage

```bash
# Count requests by endpoint
sudo awk '{print $7}' /var/log/nginx/aivision_access.log | sort | uniq -c | sort -rn

# Count unique IPs accessing public APIs
sudo grep "/api/v1/public" /var/log/nginx/aivision_access.log | awk '{print $1}' | sort -u | wc -l

# Most active IPs
sudo awk '{print $1}' /var/log/nginx/aivision_access.log | sort | uniq -c | sort -rn | head -10
```

---

## 🚀 Advanced Configuration

### Custom Frontend URL

If you want the frontend hosted on a different domain:

**Backend (.env):**
```bash
ALLOWED_ORIGINS=https://frontend.example.com,https://ocr.yourdomain.com
```

**Frontend (.env.production):**
```bash
VITE_API_URL=https://ocr.yourdomain.com
```

Rebuild frontend:
```bash
cd /opt/aivision/frontend
sudo -u aivision npm run build
sudo systemctl restart nginx
```

### Load Balancer Setup

For high traffic, use AWS Application Load Balancer:

1. Create ALB in AWS Console
2. Add EC2 instances as targets
3. Configure health checks: `/health`
4. Update DNS to point to ALB
5. Setup SSL on ALB

### Auto-Scaling

Create an Auto Scaling Group:

1. Create AMI from configured EC2 instance
2. Create Launch Template with AMI
3. Create Auto Scaling Group
4. Set min/max instances
5. Configure scaling policies based on CPU/memory

---

## 📝 Quick Reference

### URLs

```
Template Builder:
http://YOUR_EC2_IP/template-builder
https://ocr.yourdomain.com/template-builder

Simple Extraction:
http://YOUR_EC2_IP/simple-extract
https://ocr.yourdomain.com/simple-extract

API Docs:
http://YOUR_EC2_IP/docs
https://ocr.yourdomain.com/docs
```

### Key Files

```bash
# Environment config
/opt/aivision/.env

# Nginx config
/etc/nginx/sites-available/aivision

# Logs
/var/log/nginx/aivision_access.log
/var/log/nginx/aivision_error.log
/var/log/aivision/

# Service
sudo systemctl status aivision
sudo systemctl restart aivision
```

### Common Commands

```bash
# Restart services
sudo systemctl restart aivision
sudo systemctl restart nginx

# View logs
sudo journalctl -u aivision -f
sudo tail -f /var/log/nginx/aivision_access.log

# Update CORS
sudo nano /opt/aivision/.env
# Change ALLOWED_ORIGINS=*
sudo systemctl restart aivision

# Test endpoints
curl http://localhost/health
curl http://localhost/api/v1/public/templates

# Check ports
sudo lsof -i :80
sudo lsof -i :8000
```

---

## 🎯 Example Integration

### Embed in Your Website

```html
<!DOCTYPE html>
<html>
<head>
    <title>OCR Integration</title>
</head>
<body>
    <h1>Document Extraction</h1>

    <!-- Embed as iframe -->
    <iframe
        src="https://ocr.yourdomain.com/simple-extract"
        width="100%"
        height="800px"
        frameborder="0">
    </iframe>

    <!-- Or use API directly -->
    <script>
        async function extractDocument(file, templateName) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('model', 'gemini-2.0-flash-exp');

            const response = await fetch(
                `https://ocr.yourdomain.com/api/v1/public/extract/${templateName}`,
                {
                    method: 'POST',
                    body: formData
                }
            );

            return await response.json();
        }
    </script>
</body>
</html>
```

### Mobile App Integration

```javascript
// React Native example
import * as DocumentPicker from 'expo-document-picker';

async function pickAndExtract() {
    // Pick document
    const result = await DocumentPicker.getDocumentAsync({
        type: 'application/pdf'
    });

    if (result.type === 'success') {
        // Create form data
        const formData = new FormData();
        formData.append('file', {
            uri: result.uri,
            type: 'application/pdf',
            name: 'document.pdf'
        });
        formData.append('model', 'gemini-2.0-flash-exp');

        // Extract
        const response = await fetch(
            'https://ocr.yourdomain.com/api/v1/public/extract/invoice',
            {
                method: 'POST',
                body: formData
            }
        );

        const data = await response.json();
        console.log('Extracted:', data);
    }
}
```

---

## 🆘 Need Help?

- **Deployment Issues**: See `README_AWS_EC2.md`
- **Local Development**: See `README_LOCAL_WINDOWS.md`
- **API Reference**: Access `/docs` on your server
- **Logs**: `sudo journalctl -u aivision -f`

---

**🎉 Your public OCR UIs are now accessible from anywhere in the world!**

**Next Steps**:
1. Share the URL with your team
2. Integrate with your applications
3. Monitor usage and scale as needed

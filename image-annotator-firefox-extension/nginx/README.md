# NGINX Reverse Proxy for Image Annotator

This directory contains the NGINX configuration for exposing the Looking Glass backend to remote clients (LAN/WAN).

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Remote Client  │────▶│  NGINX (Port 9090)   │────▶│  Looking Glass BE   │
│  (Browser)      │     │  (192.168.122.1)     │     │  (172.16.100.174)   │
│                 │     │                      │     │  (Port 8000)        │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
```

**Network Flow:**
1. Remote PC on `192.168.122.0/24` network
2. Connects to NGINX host at `192.168.122.1:9090`
3. NGINX proxies to backend at `172.16.100.174:8000`

## Quick Start

### Prerequisites

- Docker and Docker Compose installed on the NGINX host
- Network connectivity between NGINX host and backend server
- Backend server running and healthy

### Deployment

1. **Navigate to this directory:**
   ```bash
   cd image-annotator-firefox-extension/nginx
   ```

2. **Start NGINX:**
   ```bash
   docker-compose up -d
   ```

3. **Verify it's running:**
   ```bash
   docker-compose ps
   curl http://localhost:9090/health
   # Should return: healthy
   ```

4. **Test from a remote machine:**
   ```bash
   curl http://192.168.122.1:9090/health
   ```

## Configuration

### nginx.conf

| Directive | Value | Description |
|-----------|-------|-------------|
| `listen` | `0.0.0.0:80` | Listen on all interfaces |
| `proxy_pass` | `http://172.16.100.174:8000` | Backend server address |
| `proxy_read_timeout` | `600s` | 10-minute timeout for annotation requests |
| `proxy_buffering` | `off` | Disable buffering for streaming responses |
| CORS headers | `*` | Allow all origins (for Tampermonkey) |

### docker-compose.yml

| Setting | Value | Description |
|---------|-------|-------------|
| Container name | `image-annotator-proxy` | Easy identification |
| Port mapping | `9090:80` | Host 9090 → Container 80 |
| Network | `proxy-network` | Isolated bridge network |
| Restart policy | `unless-stopped` | Auto-restart on failure |

### Changing the Backend Address

If your backend is on a different IP or port, update `nginx.conf`:

```nginx
location / {
    proxy_pass http://YOUR_BACKEND_IP:YOUR_BACKEND_PORT;
    # ... rest of config
}
```

Then restart:
```bash
docker-compose restart
```

### Changing the Exposed Port

To expose on a different port (e.g., 8080 instead of 9090), update `docker-compose.yml`:

```yaml
ports:
  - "8080:80"  # Change 9090 to your desired port
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

## Firewall Configuration

Ensure the NGINX host allows incoming connections on port 9090:

### UFW (Ubuntu)
```bash
sudo ufw allow 9090/tcp
sudo ufw reload
```

### firewalld (CentOS/RHEL)
```bash
sudo firewall-cmd --add-port=9090/tcp --permanent
sudo firewall-cmd --reload
```

### iptables
```bash
sudo iptables -A INPUT -p tcp --dport 9090 -j ACCEPT
sudo iptables-save
```

## Monitoring

### Check logs
```bash
docker-compose logs -f
```

### Check container status
```bash
docker-compose ps
```

### Test health endpoint
```bash
curl -v http://localhost:9090/health
```

### View active connections
```bash
docker exec image-annotator-proxy netstat -an | grep ESTABLISHED
```

## Security Considerations

### Current Configuration

The current setup is designed for **trusted LAN environments**:
- ✅ CORS allows all origins (`*`)
- ✅ No SSL/TLS (HTTP only)
- ✅ No rate limiting
- ✅ No IP whitelisting

### For Production/WAN Exposure

If exposing to untrusted networks, consider:

1. **Enable HTTPS:**
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       # ...
   }
   ```

2. **Add rate limiting:**
   ```nginx
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
   
   location / {
       limit_req zone=api burst=20;
       # ...
   }
   ```

3. **Restrict by IP:**
   ```nginx
   location / {
       allow 192.168.122.0/24;
       deny all;
       # ...
   }
   ```

4. **Add authentication:**
   ```nginx
   location / {
       auth_basic "Restricted";
       auth_basic_user_file /etc/nginx/.htpasswd;
       # ...
   }
   ```

## Troubleshooting

### NGINX won't start

```bash
# Check config syntax
docker exec image-annotator-proxy nginx -t

# View logs
docker-compose logs
```

### Backend unreachable

```bash
# Test from NGINX container
docker exec image-annotator-proxy curl -v http://172.16.100.174:8000/health

# Check network connectivity
docker exec image-annotator-proxy ping 172.16.100.174
```

### Connection timeout

- Increase timeout values in `nginx.conf`
- Check backend server load and performance
- Verify network bandwidth between NGINX and backend

### CORS errors

The Tampermonkey script uses `GM_xmlhttpRequest` which bypasses CORS, but if you're using the WebExtension:
- Ensure CORS headers are present in responses
- Check browser console for specific CORS errors

## Files

```
nginx/
├── nginx.conf           # NGINX server configuration
├── docker-compose.yml   # Docker Compose deployment
└── README.md            # This file
```

## Updating

To update the NGINX configuration:

1. Edit `nginx.conf`
2. Restart the container:
   ```bash
   docker-compose restart
   ```

To update the NGINX image:

```bash
docker-compose pull
docker-compose up -d --force-recreate
```

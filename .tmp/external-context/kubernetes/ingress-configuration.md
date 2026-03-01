---
source: Kubernetes Official Documentation
library: Kubernetes
package: kubernetes
topic: Ingress Configuration
fetched: 2026-02-28T00:00:00Z
official_docs: https://kubernetes.io/docs/concepts/services-networking/ingress/
---

# Kubernetes Ingress Configuration

## Overview

Ingress exposes HTTP and HTTPS routes from outside the cluster to services within the cluster. It provides Layer 7 routing, SSL termination, and name-based virtual hosting.

## Ingress Basics

### What is Ingress?

- **Not a Service**: Ingress is a collection of rules that allow inbound connections
- **Layer 7 Routing**: Routes based on HTTP host and path
- **Requires Ingress Controller**: Must deploy an ingress controller
- **Single Entry Point**: Provides centralized access to multiple services

### Ingress Controller

An ingress controller is a load balancer that implements the Ingress rules. Popular options:

- **NGINX Ingress Controller** (most popular)
- **Traefik**
- **HAProxy**
- **AWS ALB Ingress Controller**
- **GCE Ingress Controller**
- **Cert-Manager** (for automatic SSL certificates)

## Ingress Resource Structure

### Basic Ingress Example
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### Key Components

1. **metadata.name**: Ingress resource name
2. **spec.rules**: List of routing rules
3. **host**: Domain name (optional, defaults to catch-all)
4. **http.paths**: Path-based routing rules
5. **pathType**: How paths are matched (Exact, Prefix, ImplementationSpecific)
6. **backend**: Service to route traffic to

## Common Ingress Patterns

### 1. Simple Single Service
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: simple-ingress
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### 2. Path-based Routing
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-based-ingress
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### 3. Host-based Routing
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-based-ingress
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### 4. SSL/TLS Configuration
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
  annotations:
    kubernetes.io/tls-acme: "true"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls-secret
  - hosts:
    - web.example.com
    secretName: web-tls-secret
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### 5. Default Backend
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: default-backend-ingress
spec:
  defaultBackend:
    service:
      name: web-service
      port:
        number: 80
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

## Common Annotations (NGINX)

### SSL Configuration
```yaml
annotations:
  nginx.ingress.kubernetes.io/ssl-redirect: "true"
  nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
```

### Rewrite Rules
```yaml
annotations:
  nginx.ingress.kubernetes.io/rewrite-target: /$1
  nginx.ingress.kubernetes.io/use-regex: "true"
```

### Rate Limiting
```yaml
annotations:
  nginx.ingress.kubernetes.io/limit-rps: "100"
  nginx.ingress.kubernetes.io/limit-connections: "10"
```

### Authentication
```yaml
annotations:
  nginx.ingress.kubernetes.io/auth-type: basic
  nginx.ingress.kubernetes.io/auth-secret: basic-auth
  nginx.ingress.kubernetes.io/auth-realm: 'Authentication Required'
```

### Proxy Configuration
```yaml
annotations:
  nginx.ingress.kubernetes.io/proxy-body-size: "50m"
  nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
  nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
  nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
```

### Session Affinity
```yaml
annotations:
  nginx.ingress.kubernetes.io/affinity: "cookie"
  nginx.ingress.kubernetes.io/session-cookie-name: "route"
```

## Path Types

### Exact
- Matches the URL path exactly
```yaml
path: /api/v1/users
pathType: Exact
```

### Prefix
- Matches based on URL path prefix
```yaml
path: /api
pathType: Prefix
# Matches: /api, /api/, /api/users, /api/v1
```

### ImplementationSpecific
- Depends on ingress controller implementation
- Default for many controllers

## Best Practices

### 1. Use TLS Everywhere
- Always configure TLS for production
- Use cert-manager for automatic certificate management
- Force HTTPS redirects

### 2. Organize by Domain
- Separate ingress resources by domain
- Use host-based routing for multiple services

### 3. Implement Rate Limiting
- Protect against abuse
- Configure appropriate limits per service

### 4. Use Annotations Wisely
- Document custom annotations
- Keep configuration consistent

### 5. Implement Health Checks
- Configure readiness probes
- Use ingress health check annotations

### 6. Set Timeouts Appropriately
- Adjust proxy timeouts based on service needs
- Prevent hanging connections

### 7. Configure Logging
- Enable access logs
- Monitor for errors and anomalies

## Ingress vs LoadBalancer

| Feature | Ingress | LoadBalancer |
|---------|---------|--------------|
| Layer | Layer 7 (HTTP/HTTPS) | Layer 4 (TCP/UDP) |
| Routing | Host/path-based | Port-based |
| SSL Termination | ✅ | ❌ (usually) |
| Cost | Lower (single LB) | Higher (per service) |
| Complexity | Higher | Lower |
| Best For | HTTP/HTTPS services | Any protocol |

## Troubleshooting

### Ingress Not Working
1. Verify ingress controller is running
2. Check ingress resource exists: `kubectl get ingress`
3. Verify annotations are correct
4. Check service backend exists

### SSL Certificate Issues
1. Verify TLS secret exists
2. Check certificate expiration
3. Review cert-manager logs
4. Verify host matches certificate

### 502 Bad Gateway
1. Check backend service is running
2. Verify readiness probes pass
3. Check service selector matches pods
4. Review ingress controller logs

### 404 Not Found
1. Verify path configuration
2. Check host header matches
3. Review ingress rules
4. Verify backend service port

## Recommended Setup for Web Applications

```yaml
# Production setup with TLS
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: production-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - app.example.com
    secretName: app-tls-secret
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

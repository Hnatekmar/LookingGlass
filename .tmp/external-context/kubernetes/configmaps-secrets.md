---
source: Kubernetes Official Documentation
library: Kubernetes
package: kubernetes
topic: ConfigMaps and Secrets
fetched: 2026-02-28T00:00:00Z
official_docs: https://kubernetes.io/docs/concepts/configuration/configmap/ | https://kubernetes.io/docs/concepts/configuration/secret/
---

# ConfigMaps and Secrets Management

## Overview

ConfigMaps and Secrets are used to inject configuration data into pods. They decouple configuration from container images, making applications more portable and secure.

## ConfigMaps

### What is a ConfigMap?

- Stores non-confidential configuration data in key-value pairs
- Can be consumed by pods as environment variables, command-line arguments, or configuration files
- Ideal for configuration that might change

### Creating ConfigMaps

#### 1. From Literal Values
```bash
kubectl create configmap app-config \
  --from-literal=APP_COLOR=blue \
  --from-literal=APP_MODE=prod
```

#### 2. From Files
```bash
kubectl create configmap app-config \
  --from-file=config.properties \
  --from-file=app.properties
```

#### 3. From Directory
```bash
kubectl create configmap app-config \
  --from-file=/path/to/directory
```

#### 4. Using YAML
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_COLOR: blue
  APP_MODE: prod
  database_url: postgresql://db:5432/app
  # Multi-line configuration
  nginx.conf: |
    server {
      listen 80;
      server_name localhost;
      location / {
        root /usr/share/nginx/html;
      }
    }
```

### Using ConfigMaps in Pods

#### 1. As Environment Variables
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: web
    image: nginx
    env:
    - name: APP_COLOR
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: APP_COLOR
    envFrom:
    - configMapRef:
        name: app-config
```

#### 2. As Volume Mounts
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: web
    image: nginx
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      # Optional: Select specific items
      items:
      - key: nginx.conf
        path: nginx.conf
```

#### 3. As Command Arguments
```yaml
spec:
  containers:
  - name: web
    image: nginx
    command: ["/bin/sh"]
    args: ["-c", "echo $APP_COLOR && exec nginx -g 'daemon off;'"]
    envFrom:
    - configMapRef:
        name: app-config
```

### ConfigMap Best Practices

1. **Use descriptive names**: `app-name-config` not `config1`
2. **Namespace-specific**: Create in appropriate namespaces
3. **Version control**: Store manifests in Git
4. **Update strategy**: Rolling updates for ConfigMap changes
5. **Validation**: Validate config before deployment
6. **Documentation**: Document expected keys and values

## Secrets

### What is a Secret?

- Stores sensitive information (passwords, tokens, keys)
- Base64 encoded (NOT encrypted by default)
- Can be consumed like ConfigMaps
- Better security practices recommended

### Creating Secrets

#### 1. From Literal Values
```bash
kubectl create secret generic db-secret \
  --from-literal=DB_PASSWORD=secret123 \
  --from-literal=DB_USER=admin
```

#### 2. From Files
```bash
kubectl create secret generic tls-secret \
  --from-file=tls.crt \
  --from-file=tls.key
```

#### 3. Using YAML (Base64 Encoded)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  # echo -n "password" | base64
  DB_PASSWORD: cGFzc3dvcmQ=
  # echo -n "admin" | base64
  DB_USER: YWRtaW4=
```

#### 4. Using YAML (Unencoded - Kubernetes 1.7+)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
stringData:
  DB_PASSWORD: password
  DB_USER: admin
```

### Secret Types

#### 1. Opaque (Default)
```yaml
type: Opaque
data:
  username: YWRtaW4=
  password: MWYyZDFlMmU2N2Rm
```

#### 2. kubernetes.io/basic-auth
```yaml
type: kubernetes.io/basic-auth
data:
  username: YWRtaW4=
  password: MWYyZDFlMmU2N2Rm
```

#### 3. kubernetes.io/ssh-auth
```yaml
type: kubernetes.io/ssh-auth
data:
  ssh-privatekey: <base64 encoded key>
```

#### 4. kubernetes.io/tls
```yaml
type: kubernetes.io/tls
data:
  tls.crt: <base64 encoded cert>
  tls.key: <base64 encoded key>
```

#### 5. docker-registry
```yaml
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64 encoded docker config>
```

### Using Secrets in Pods

#### 1. As Environment Variables
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: web
    image: nginx
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: DB_PASSWORD
    envFrom:
    - secretRef:
        name: app-secret
```

#### 2. As Volume Mounts
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: web
    image: nginx
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: app-secret
      # Optional: Set permissions
      defaultMode: 0400
```

#### 3. In Image Pull Secrets
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: web
    image: private-registry/app:latest
  imagePullSecrets:
  - name: registry-secret
```

### Secret Security Best Practices

#### 1. Enable Encryption at Rest
```yaml
# api-server configuration
encryptingConfig:
  apiVersion: apiserver.config.k8s.io/v1
  kind: EncryptionConfiguration
  resources:
  - resources:
    - secrets
    providers:
    - aescbc:
        keys:
        - name: key1
          secret: <base64 encoded key>
    - identity: {}
```

#### 2. Use External Secret Management
- **HashiCorp Vault**
- **AWS Secrets Manager**
- **Azure Key Vault**
- **Google Secret Manager**

#### 3. Implement RBAC
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "watch", "list"]
```

#### 4. Use Sealed Secrets or External Operators
- Encrypt secrets in Git
- Decrypt only in cluster
- Tools: Bitnami Sealed Secrets, External Secrets Operator

#### 5. Avoid Committing Secrets
```bash
# Never do this
kubectl create secret generic db-secret --from-literal=password=secret123 | kubectl apply -f -
# In CI/CD pipelines, use secret management tools
```

### Common Patterns

#### Database Connection
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:
  username: app-user
  password: $(generate-secure-password)
  host: postgresql://db:5432
---
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: web
    image: myapp:latest
    env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: host
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password
```

#### TLS Configuration
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
stringData:
  tls.crt: |
    -----BEGIN CERTIFICATE-----
    ...
    -----END CERTIFICATE-----
  tls.key: |
    -----BEGIN PRIVATE KEY-----
    ...
    -----END PRIVATE KEY-----
```

#### API Keys
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
type: Opaque
stringData:
  stripe-api-key: sk_live_xxx
  sendgrid-api-key: SG.xxx
  aws-access-key-id: AKIAIOSFODNN7EXAMPLE
  aws-secret-access-key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

## ConfigMap vs Secret

| Feature | ConfigMap | Secret |
|---------|-----------|--------|
| Purpose | Non-sensitive config | Sensitive data |
| Encoding | Plain text | Base64 |
| Security | Low | Medium (enable encryption) |
| Use Cases | App config, env vars | Passwords, tokens, keys |
| Visibility | Clear text | Base64 (easily decoded) |

## Troubleshooting

### ConfigMap/Secret Not Available
1. Verify it exists in correct namespace
2. Check pod is using correct namespace
3. Verify key names match
4. Check RBAC permissions

### Mounting Issues
1. Verify volume mount path
2. Check secret/configmap name
3. Review pod events: `kubectl describe pod <name>`
4. Check permissions on mounted files

### Update Not Reflected
1. ConfigMaps/Secrets updates require pod restart
2. Use rolling update strategy
3. Consider using mounted volumes (updates eventually)
4. Use tools like Reloader for automatic restarts

## Best Practices Summary

### ConfigMaps
- ✅ Use for non-sensitive configuration
- ✅ Version control manifests
- ✅ Use namespaces for isolation
- ✅ Validate configuration before deployment
- ✅ Document expected keys

### Secrets
- ✅ Never commit plain text secrets
- ✅ Enable encryption at rest
- ✅ Use external secret management for production
- ✅ Implement RBAC restrictions
- ✅ Rotate secrets regularly
- ✅ Audit secret access
- ✅ Use sealed secrets for GitOps

### General
- ✅ Use specific keys (not all-in-one)
- ✅ Follow naming conventions
- ✅ Test in staging first
- ✅ Monitor for exposure
- ✅ Use .gitignore for local secrets

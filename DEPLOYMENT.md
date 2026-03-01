# Looking Glass Deployment Quick Reference

## Helm Chart

### Basic Installation

```bash
helm install looking-glass ./charts/looking-glass \
  --namespace looking-glass \
  --create-namespace \
  --set secrets.imageModel="qwen3-8b-instruct" \
  --set secrets.translationModel="nemotron-3-nano" \
  --set secrets.imageModelUrl="https://your-model-url.com/v1" \
  --set secrets.translationModelUrl="https://your-translation-model-url.com/v1"
```

### Production Installation (with custom values)

```bash
helm install looking-glass ./charts/looking-glass \
  -f charts/looking-glass/values-production.yaml \
  --namespace looking-glass \
  --create-namespace
```

### Upgrade

```bash
helm upgrade looking-glass ./charts/looking-glass \
  -f charts/looking-glass/values-production.yaml \
  --namespace looking-glass
```

### Uninstall

```bash
helm uninstall looking-glass --namespace looking-glass
```

### Access the Service

```bash
# Port-forward (ClusterIP)
kubectl port-forward svc/looking-glass 8000:8000 -n looking-glass

# View logs
kubectl logs -f deployment/looking-glass -n looking-glass

# Check status
kubectl get pods -n looking-glass
kubectl get svc -n looking-glass
```

## ArgoCD

### Apply ArgoCD Application

```bash
kubectl apply -f argocd-application.yaml
```

### Monitor in ArgoCD UI

```bash
# Port-forward ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### ArgoCD CLI

```bash
# Login to ArgoCD
argocd login localhost:8080

# Check application status
argocd app get looking-glass

# Sync application
argocd app sync looking-glass

# Pause auto-sync
argocd app set looking-glass --sync-policy none
```

## Configuration

### Required Secrets

All secrets must be set before deployment:

- `secrets.imageModel` - Image/OCR model name
- `secrets.translationModel` - Translation model name
- `secrets.imageModelUrl` - Image model API endpoint
- `secrets.translationModelUrl` - Translation model API endpoint

### Optional Configuration

```yaml
# Production values (charts/looking-glass/values-production.yaml)
replicaCount: 3

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: looking-glass.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: looking-glass-tls
      hosts:
        - looking-glass.example.com

pdb:
  enabled: true
  minAvailable: 1
```

## Troubleshooting

### Pod Stuck in Pending

```bash
kubectl describe pod <pod-name> -n looking-glass
kubectl get events -n looking-glass --sort-by='.lastTimestamp'
```

### Pod CrashLoopBackOff

```bash
kubectl logs deployment/looking-glass -n looking-glass --previous
kubectl describe deployment/looking-glass -n looking-glass
```

### Health Check Failures

```bash
# Check if endpoint is accessible
kubectl exec -it <pod-name> -n looking-glass -- curl -s http://localhost:8000/docs

# Check resource usage
kubectl top pods -n looking-glass
```

## Security Best Practices

1. **Never commit secrets** - Use external secrets management for production
2. **Enable Pod Security** - Non-root user, read-only filesystem (enabled by default)
3. **Use HTTPS** - Configure TLS in Ingress
4. **Network Policies** - Restrict pod-to-pod communication
5. **Resource Limits** - Prevent resource exhaustion

## External Secrets (Production)

For production, use External Secrets Operator:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: looking-glass-secrets
  namespace: looking-glass
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-backend
  target:
    name: looking-glass-secrets
  data:
    - secretKey: IMAGE_MODEL
      remoteRef:
        key: looking-glass
        property: image_model
    # ... more secrets
```

Then update `values-production.yaml`:
```yaml
secrets:
  imageModel: ""  # Leave empty, will be populated by ExternalSecret
  translationModel: ""
  imageModelUrl: ""
  translationModelUrl: ""
```

## Chart Structure

```
charts/looking-glass/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default values
├── values-production.yaml  # Production example
├── values.schema.json      # Validation schema
└── templates/
    ├── _helpers.tpl        # Template helpers
    ├── namespace.yaml      # Optional namespace
    ├── configmap.yaml      # Non-sensitive config
    ├── secret.yaml         # Sensitive config
    ├── deployment.yaml     # Main deployment
    ├── service.yaml        # Service
    ├── ingress.yaml        # Ingress (optional)
    ├── pdb.yaml            # PodDisruptionBudget (optional)
    ├── serviceaccount.yaml # ServiceAccount
    └── NOTES.txt           # Post-install notes
```

## API Endpoints

Once deployed:

- **API**: `http://localhost:8000/` (via port-forward) or `https://looking-glass.example.com/` (via Ingress)
- **Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Health**: `http://localhost:8000/health` (if configured)

## Next Steps

1. ✅ Helm chart created and validated
2. ✅ ArgoCD application configured
3. ✅ Production values provided
4. ⏳ Update repository URL in `argocd-application.yaml`
5. ⏳ Configure secrets for your environment
6. ⏳ Set up external secrets management (production)
7. ⏳ Configure Ingress and TLS
8. ⏳ Deploy and test

# Optional Lightweight Kubernetes Evidence

The assessment implementation uses Docker Compose. This folder demonstrates how the modular deployment could be moved to K3s or Kind.

The manifest is intentionally a development example. Before real deployment, replace local images and plain ConfigMap values with a registry, Secrets, persistent storage classes, ingress TLS and network policies.

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/globalpay.yaml
```

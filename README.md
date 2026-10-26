# Sample Shipping HTTP Service

A minimal Python HTTP service intended to demonstrate containerization and Helm deployment to AWS EKS. It uses only Python's standard library.

## Endpoints

- `GET /` and `GET /api/shipping`: service status and metadata as JSON
- `GET /healthz`: liveness endpoint
- `GET /readyz`: readiness endpoint

## Run locally

```bash
python3 app.py
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/healthz
```

## Build and test the container

```bash
docker build -t shipping:1.0.0 .
docker run --rm -p 8080:8080 shipping:1.0.0
curl http://127.0.0.1:8080/api/shipping
```

## Deploy to EKS

1. Create an ECR repository (once):
   ```bash
   aws ecr create-repository --repository-name shipping --region ap-south-1
   ```
2. Set your AWS account ID and region:
   ```bash
   export AWS_REGION=ap-south-1
   export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
   export ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/shipping"
   ```
3. Authenticate, build, and push:
   ```bash
   aws ecr get-login-password --region "$AWS_REGION" | \
     docker login --username AWS --password-stdin \
       "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
   docker build -t shipping:1.0.0 .
   docker tag shipping:1.0.0 "${ECR_URI}:1.0.0"
   docker push "${ECR_URI}:1.0.0"
   ```
4. Make sure `kubectl` is connected to the intended EKS cluster:
   ```bash
   kubectl config current-context
   kubectl get nodes
   ```
5. Deploy the chart from the `shipping/` directory:
   ```bash
   helm lint .
   helm template shipping . \
     --set image.repository="$ECR_URI" \
     --set image.tag=1.0.0
   helm upgrade --install shipping . \
     --namespace shipping --create-namespace \
     --set image.repository="$ECR_URI" \
     --set image.tag=1.0.0
   ```
6. Validate and test:
   ```bash
   kubectl -n shipping rollout status deployment/shipping-shipping
   kubectl -n shipping get pods,svc
   kubectl -n shipping port-forward svc/shipping-shipping 8080:8080
   # In another terminal:
   curl http://127.0.0.1:8080/api/shipping
   ```

The service defaults to `ClusterIP`; port-forward is used for initial validation. Configure an Ingress or LoadBalancer only if external access is needed. For private ECR images, EKS nodes must have permission to pull from ECR. In standard EKS setups, node IAM permissions commonly provide this.

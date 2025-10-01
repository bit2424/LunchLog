## LunchLog backend: AWS deployment via CloudFormation (ECS Fargate)

This guide deploys the Django REST backend, Celery worker, and Celery Beat into ECS Fargate, with RDS Postgres, ElastiCache Redis, and S3 buckets for static and media. No ALB; the backend service receives a public IP directly.

### Prerequisites
- AWS CLI v2 configured with sufficient permissions (ECS, EC2/VPC, RDS, ElastiCache, S3, IAM, Logs, Secrets Manager, CloudFormation)
- An ECR repository with your built image pushed (single image used by all tasks)
- A domain is optional. Without it, you will use the service public IP

### Map env.example to AWS
The stack uses parameters and Secrets Manager entries mapped from these keys:

- Database
  - `DATABASE_URL`: created as a secret from the RDS endpoint in the stack
  - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: managed by RDS and a generated master password secret
- Django
  - `SECRET_KEY`: generated into Secrets Manager by the stack
  - `DEBUG`: not used in stack; keep it `False` in production builds
  - `ALLOWED_HOSTS`: set via stack parameter; defaults to `*`. Set to your domain/IP
- CORS
  - `CORS_ALLOWED_ORIGINS`: configure inside Django settings; not parameterized here
- AWS S3
  - Buckets are created for static and media. Region is passed to container via `AWS_S3_REGION_NAME`
- Celery
  - `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`: created as a secret from ElastiCache endpoint
- Google Places API
  - `GOOGLE_PLACES_API_KEY`: if needed, add it to Secrets Manager and reference in task defs

If you already have a `.env` can find the template here: [.env.example](.env.example) file, you can use it to set the env vars by doing the following:

```bash
export $(cat .env | xargs)
```

If you need additional env vars, either parameterize the template or create Secrets in Secrets Manager and add to the ECS task definitions.

### Secrets and environment variables
- The stack automatically creates and wires these secrets (auto-generated unique names):
  - `SECRET_KEY`: Django secret key (generated)
  - `DATABASE_URL`: PostgreSQL connection string (built from RDS endpoint)
  - `REDIS_URL`: Redis connection string (built from ElastiCache endpoint)
  - RDS master password: Internal secret used to construct DATABASE_URL

- List secrets created by the stack:
```bash
aws secretsmanager list-secrets --region $AWS_REGION \
  --query "SecretList[?contains(Description, 'Django') || contains(Description, 'DATABASE_URL') || contains(Description, 'Redis')].[Name,Description]" \
  --output table
```

- View a secret value (get the name from list above):
```bash
aws secretsmanager get-secret-value \
  --secret-id SECRET_NAME_FROM_LIST \
  --region $AWS_REGION \
  --query SecretString --output text | cat
```

- Create your own secret (example for `GOOGLE_PLACES_API_KEY`):
```bash
aws secretsmanager create-secret \
  --name lunchlog/prod/app/GOOGLE_PLACES_API_KEY \
  --secret-string 'your-google-places-api-key' \
  --region $AWS_REGION
```

- Notes:
  - S3 access is via the ECS task role; no access keys are needed in env vars.
  - Rotating a Secrets Manager value takes effect on new tasks; restart services to pick up changes.

### Build and push image to ECR
Replace placeholders with your values:

```bash
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=eu-north-1
export REPO_NAME=lunchlog

aws ecr create-repository --repository-name $REPO_NAME --region $AWS_REGION || true
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -f Dockerfile.prod -t $REPO_NAME .
docker tag $REPO_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest
```

### Deploy stack

```bash
export STACK_NAME=lunchlog-prod
export IMAGE_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest
export GOOGLE_PLACES_API_KEY=your-google-places-api-key

aws cloudformation deploy \
  --stack-name $STACK_NAME \
  --region $AWS_REGION \
  --capabilities CAPABILITY_NAMED_IAM \
  --template-file deploy/cloudformation/ecs.yml \
  --parameter-overrides \
    ProjectName=lunchlog \
    EnvironmentName=prod \
    AppImageUri=$IMAGE_URI \
    AllowedHosts="*" \
    DjangoSettingsModule=lunchlog.settings \
    GooglePlacesApiKey=$GOOGLE_PLACES_API_KEY
```

Wait until status is CREATE_COMPLETE:

```bash
aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --query 'Stacks[0].StackStatus' --output text | cat
```

#### Update services
```bash
export CLUSTER=lunchlog-prod-cluster
export SERVICE=lunchlog-prod-backend
aws ecs update-service \
  --cluster $CLUSTER \
  --service $SERVICE \
  --region $AWS_REGION \
  --force-new-deployment
```

### Get backend service public IP
No ALB is used; tasks have public IPs. Retrieve them:

```bash
export CLUSTER= lunchlog-prod-cluster
export SERVICE=lunchlog-prod-backend
aws ecs list-tasks --cluster $CLUSTER --service-name $SERVICE --region $AWS_REGION --query 'taskArns' --output text | xargs -n1 -I{} aws ecs describe-tasks --cluster $CLUSTER --tasks {} --region $AWS_REGION --query 'tasks[*].attachments[0].details[?name==`publicIPv4Address`].value' --output text | cat
```

Your API will be available at `http://PUBLIC_IP:8000` (or your configured container port).

### Running migrations and collectstatic

Execute command:
```bash
export CLUSTER=lunchlog-prod-cluster
export SERVICE=lunchlog-prod-backend
export TASK_DEF=$(aws ecs describe-task-definition --task-definition lunchlog-prod-backend --region $AWS_REGION --query 'taskDefinition.taskDefinitionArn' --output text)

aws ecs execute-command \
  --cluster $CLUSTER \
  --task $TASK_DEF \
  --container backend \
  --command "python manage.py migrate && python manage.py collectstatic --noinput"
```

### Notes
- This template sets public IPs for all services for simplicity. For production hardening, prefer private subnets + NAT + ALB.
- Adjust instance sizes and storage for your workload.
- Set `AllowedHosts` to a specific domain or IP.
- To pass more secrets, create them in Secrets Manager and reference them in task definitions.


# AWS Lambda Setup Guide

This guide walks you through deploying StartPage as an AWS Lambda function that runs on a schedule using CloudFormation.

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- Python 3.12
- Poetry installed

## Initial Setup

### 1. Create an S3 Bucket for Deployment Artifacts

```bash
aws s3 mb s3://your-startpage-bucket --region us-east-1
```

### 2. Build and Upload the Lambda Package

```bash
# Install the Lambda build plugin
poetry self add poetry-plugin-lambda-build

# Build the Lambda package
poetry build-lambda

# Upload to S3
aws s3 cp package.zip s3://your-startpage-bucket/startpage/package.zip
```

### 3. Deploy the CloudFormation Stack

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name startpage \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    S3Bucket=your-startpage-bucket \
    S3Key=startpage/package.zip \
    NotionToken=secret_xxx \
    PageId=your_page_id \
    BlockId=your_block_id \
    City=London \
    ICloudUsername=your@icloud.com \
    ICloudAppPassword=xxxx-xxxx-xxxx-xxxx \
    Timezone=Europe/London \
    ScheduleExpression='cron(0 6 * * ? *)'
```

The CloudFormation stack creates:
- **Lambda Function** with your code from S3
- **IAM Role** with basic Lambda execution permissions
- **EventBridge Rule** for daily scheduling
- **CloudWatch Log Group** with 7-day retention

### 4. Test Your Lambda Function

```bash
# Invoke the function manually
aws lambda invoke \
  --function-name startpage \
  --invocation-type RequestResponse \
  --log-type Tail \
  output.json

# View the response
cat output.json

# View logs
aws logs tail /aws/lambda/startpage --follow
```

## Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings -> Secrets and variables -> Actions):

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) |
| `S3_BUCKET` | S3 bucket name for package.zip |
| `S3_KEY` | S3 key (default: `startpage/package.zip`) |
| `NOTION_TOKEN` | Notion API token |
| `PAGE_ID` | Notion page ID |
| `BLOCK_ID` | Notion block ID |
| `CITY` | City for weather |
| `ICLOUD_USERNAME` | iCloud email |
| `ICLOUD_APP_PASSWORD` | iCloud app-specific password |
| `TIMEZONE` | IANA timezone |

## Get AWS Credentials for GitHub Actions

Create an IAM user with permissions for S3 upload and CloudFormation deployment:

```bash
cat > deploy-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-startpage-bucket/startpage/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:GetTemplate",
        "cloudformation:CreateChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:DeleteChangeSet"
      ],
      "Resource": "arn:aws:cloudformation:*:*:stack/startpage/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
        "lambda:AddPermission",
        "lambda:RemovePermission"
      ],
      "Resource": "arn:aws:lambda:*:*:function:startpage"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:GetRole",
        "iam:PassRole",
        "iam:DeleteRole"
      ],
      "Resource": "arn:aws:iam::*:role/startpage-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:PutTargets",
        "events:RemoveTargets",
        "events:DeleteRule",
        "events:DescribeRule"
      ],
      "Resource": "arn:aws:events:*:*:rule/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:PutRetentionPolicy"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/startpage:*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name StartPageDeployPolicy \
  --policy-document file://deploy-policy.json

aws iam create-user --user-name github-actions-startpage

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws iam attach-user-policy \
  --user-name github-actions-startpage \
  --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/StartPageDeployPolicy"

aws iam create-access-key --user-name github-actions-startpage
```

Save the **AccessKeyId** and **SecretAccessKey** as GitHub secrets.

## Deployment Workflow

The GitHub Actions workflow automatically deploys to Lambda when a pull request is merged to `main`:

1. Builds a Lambda package using `poetry-plugin-lambda-build`
2. Uploads `package.zip` to S3
3. Deploys the CloudFormation stack (creates/updates Lambda, EventBridge, IAM role)

## Manual Deployment

```bash
# Build
poetry build-lambda

# Upload and deploy
aws s3 cp package.zip s3://your-startpage-bucket/startpage/package.zip
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name startpage \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides S3Bucket=your-startpage-bucket ...
```

Or use the Makefile:

```bash
make deploy \
  S3_BUCKET=your-startpage-bucket \
  S3_KEY=startpage/package.zip \
  NOTION_TOKEN=... \
  PAGE_ID=... \
  BLOCK_ID=... \
  CITY=London \
  ICLOUD_USERNAME=... \
  ICLOUD_APP_PASSWORD=... \
  TIMEZONE=Europe/London
```

## Monitoring

```bash
# View recent logs
aws logs tail /aws/lambda/startpage --since 1h

# Follow logs in real-time
aws logs tail /aws/lambda/startpage --follow
```

## Schedule Configuration

The default schedule runs daily at 6:00 AM UTC. To change it, update the `ScheduleExpression` parameter and redeploy:

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name startpage \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides ScheduleExpression='cron(0 8 * * ? *)' ...
```

Common cron expressions:
- `cron(0 6 * * ? *)` - Daily at 6 AM UTC
- `cron(0 8 * * ? *)` - Daily at 8 AM UTC
- `cron(0 */6 * * ? *)` - Every 6 hours
- `cron(0 0 * * MON *)` - Every Monday at midnight

## Troubleshooting

**Function timeout:** Increase the timeout in `template.yaml` (currently 300s, max 900s).

**Memory issues:** Increase `MemorySize` in `template.yaml` (currently 512 MB).

**Missing dependencies:** Ensure all dependencies are listed in `pyproject.toml` under `[project.dependencies]`.

**Environment variables:** Verify all parameters were passed correctly during CloudFormation deploy.

**Calendar issues:** Make sure your iCloud app-specific password is valid. Generate one at appleid.apple.com.

## Cost Estimation

With the default daily schedule:
- Lambda executions: ~30/month (free tier covers 1M requests)
- Compute time: ~30 seconds/run = 15 minutes/month (free tier covers 400,000 GB-seconds)
- S3: < 1 MB storage for package.zip (free tier covers 5 GB)
- CloudWatch Logs: Minimal cost (7-day retention)

**Expected monthly cost: $0** (within free tier limits)

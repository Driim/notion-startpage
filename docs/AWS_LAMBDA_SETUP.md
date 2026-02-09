# AWS Lambda Setup Guide

This guide walks you through deploying StartPage as an AWS Lambda function that runs on a schedule.

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- Python 3.13
- Poetry installed

## Initial Setup

### 1. Create Lambda Function

You can create the Lambda function using AWS SAM (recommended) or manually via AWS Console/CLI.

#### Option A: Using AWS SAM (Recommended)

```bash
# Install AWS SAM CLI
brew install aws-sam-cli  # macOS
# or follow instructions at https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

# Deploy the application
sam deploy --guided
```

During the guided deployment, you'll be prompted for:
- Stack Name: `startpage`
- AWS Region: Your preferred region (e.g., `us-east-1`)
- NotionToken: Your Notion API token
- PageId: Your Notion page ID
- BlockId: Your Notion block ID for fact updates
- City: City for weather (e.g., `London`)
- ICloudUsername: Your iCloud email
- ICloudAppPassword: Your iCloud app-specific password
- Timezone: Your timezone (e.g., `Europe/London`)
- ScheduleExpression: Cron expression for scheduling (default: `cron(0 6 * * ? *)` - daily at 6 AM UTC)

#### Option B: Manual Setup via AWS Console

1. **Create Lambda Function**:
   - Go to AWS Lambda Console
   - Click "Create function"
   - Choose "Author from scratch"
   - Function name: `startpage`
   - Runtime: Python 3.13
   - Architecture: x86_64
   - Execution role: Create a new role with basic Lambda permissions

2. **Configure Function**:
   - Memory: 512 MB
   - Timeout: 5 minutes (300 seconds)
   - Handler: `lambda_handler.lambda_handler`

3. **Set Environment Variables**:
   Add these environment variables in the Lambda configuration:
   ```
   NOTION_TOKEN=your_notion_token
   PAGE_ID=your_page_id
   BLOCK_ID=your_block_id
   CITY=London
   ICLOUD_USERNAME=your_icloud_email
   ICLOUD_APP_PASSWORD=your_app_specific_password
   TIMEZONE=Europe/London
   ```

4. **Create EventBridge Schedule**:
   - Go to Amazon EventBridge Console
   - Navigate to "Rules" under "Buses"
   - Click "Create rule"
   - Name: `startpage-daily-trigger`
   - Rule type: Schedule
   - Schedule pattern: Cron expression - `cron(0 6 * * ? *)` (runs daily at 6 AM UTC)
   - Target: AWS Lambda function
   - Function: `startpage`

### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1  # or your preferred region
LAMBDA_FUNCTION_NAME=startpage  # or your function name from SAM
```

### 3. Get AWS Credentials

Create an IAM user for GitHub Actions with Lambda update permissions:

```bash
# Create IAM policy
cat > lambda-deploy-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:startpage"
    }
  ]
}
EOF

# Create policy
aws iam create-policy \
  --policy-name StartPageLambdaDeployPolicy \
  --policy-document file://lambda-deploy-policy.json

# Create IAM user
aws iam create-user --user-name github-actions-startpage

# Attach policy to user
aws iam attach-user-policy \
  --user-name github-actions-startpage \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/StartPageLambdaDeployPolicy

# Create access key
aws iam create-access-key --user-name github-actions-startpage
```

Save the Access Key ID and Secret Access Key as GitHub secrets.

## Deployment Workflow

The GitHub Actions workflow automatically deploys to Lambda when:
- A pull request is merged to `main` branch

The workflow:
1. Installs Poetry and the Lambda build plugin
2. Installs dependencies
3. Builds a Lambda deployment package using `poetry-plugin-lambda-build`
4. Uploads the package to AWS Lambda

## Manual Deployment

To deploy manually from your local machine:

```bash
# Install the Lambda build plugin
poetry self add poetry-plugin-lambda-build

# Build the Lambda package
poetry build-lambda

# Deploy to AWS Lambda
aws lambda update-function-code \
  --function-name startpage \
  --zip-file fileb://package.zip
```

## Testing

Test your Lambda function:

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

## Monitoring

View Lambda execution logs:

```bash
# View recent logs
aws logs tail /aws/lambda/startpage --since 1h

# Follow logs in real-time
aws logs tail /aws/lambda/startpage --follow
```

Or use AWS CloudWatch Console:
- Go to CloudWatch → Log groups
- Find `/aws/lambda/startpage`

## Schedule Configuration

The default schedule runs daily at 6:00 AM UTC. To change the schedule:

### If using SAM:
Update the `ScheduleExpression` parameter in `template.yaml` and redeploy:
```bash
sam deploy
```

### If using EventBridge directly:
1. Go to Amazon EventBridge Console
2. Find your rule (`startpage-daily-trigger`)
3. Edit the schedule pattern

Common cron expressions:
- `cron(0 6 * * ? *)` - Daily at 6 AM UTC
- `cron(0 8 * * ? *)` - Daily at 8 AM UTC
- `cron(0 */6 * * ? *)` - Every 6 hours
- `cron(0 0 * * MON *)` - Every Monday at midnight

## Troubleshooting

### Function timeout
If the function times out, increase the timeout in Lambda configuration (max 15 minutes).

### Memory issues
If you see out-of-memory errors, increase the memory allocation (currently 512 MB).

### Missing dependencies
Ensure all dependencies are listed in `pyproject.toml` under `[project.dependencies]`.

### Environment variables
Verify all required environment variables are set in Lambda configuration.

### Calendar issues
Make sure your iCloud app-specific password is valid. Generate one at appleid.apple.com.

## Cost Estimation

With the default daily schedule:
- Lambda executions: ~30/month (free tier covers 1M requests)
- Compute time: ~30 seconds/run = 15 minutes/month (free tier covers 400,000 GB-seconds)
- CloudWatch Logs: Minimal cost (7-day retention)

**Expected monthly cost: $0** (within free tier limits)

## Security Best Practices

1. **Secrets Management**: Consider using AWS Secrets Manager instead of environment variables for sensitive data
2. **IAM Permissions**: Follow principle of least privilege for Lambda execution role
3. **VPC**: If needed, configure Lambda to run in a VPC
4. **Monitoring**: Set up CloudWatch alarms for function errors

## Next Steps

- Set up CloudWatch alarms for function failures
- Add SNS notifications for errors
- Consider using AWS Secrets Manager for credentials
- Enable AWS X-Ray for tracing (optional)

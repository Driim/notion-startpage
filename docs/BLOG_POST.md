# Building an Automated Daily Dashboard in Notion with AWS Lambda

## Introduction

I've always wanted a personalized dashboard that greets me every morning with relevant information: today's weather, my calendar events, currency rates, and curated tech news. Instead of checking multiple apps, I built **StartPage** - an automated system that aggregates data from various sources and publishes it daily to a Notion page.

The best part? It runs completely serverless on AWS Lambda, costing virtually nothing (within the free tier) and requiring zero maintenance. In this guide, I'll show you how to set up your own automated Notion dashboard from scratch.

**What you'll build:**
- 🌤️ Daily weather updates for your city
- 📅 Today's calendar events from iCloud
- 💱 Currency and cryptocurrency rates
- 📰 Curated tech news from RSS feeds
- 🎲 A random interesting fact to start your day

**Tech stack:**
- Python 3.12 with asyncio for concurrent data fetching
- Notion API for publishing content
- AWS Lambda for serverless execution
- AWS CloudFormation for infrastructure as code
- AWS EventBridge for daily scheduling
- GitHub Actions for CI/CD

Let's dive in!

---

## Part 1: Understanding the Project

StartPage is a Python application that:
1. Fetches data concurrently from multiple APIs (weather, calendar, RSS feeds, currency rates)
2. Formats the data as Notion blocks
3. Publishes everything to your Notion page as a daily summary
4. Updates a "fact of the day" callout block

The architecture is simple yet powerful:

**Runtime:**
```
┌─────────────────┐
│  EventBridge    │  Triggers daily at 6 AM UTC
│  (Scheduler)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AWS Lambda     │  Runs StartPage application
│  (Python 3.12)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  Concurrent Data Fetching (asyncio.gather)      │
├──────────┬──────────┬──────────┬──────────┬─────┤
│ Weather  │ Calendar │ Currency │   RSS    │ Fact│
└──────────┴──────────┴──────────┴──────────┴─────┘
         │
         ▼
┌─────────────────┐
│   Notion API    │  Publishes formatted blocks
└─────────────────┘
```

**Deployment:**
```
┌─────────────────┐     ┌─────────────────┐
│ GitHub Actions  │────▶│   S3 Bucket     │  Stores package.zip
│ (CI/CD)         │     └────────┬────────┘
└────────┬────────┘              │
         │                       ▼
         │              ┌─────────────────┐
         └─────────────▶│ CloudFormation  │  Deploys infrastructure
                        │ (IaC)           │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  Lambda  │ │EventBridge│ │CloudWatch│
              └──────────┘ └──────────┘ └──────────┘
```

The entire execution takes about 10-15 seconds, well within Lambda's free tier limits.

---

## Part 2: Setting Up Your Notion Page

### Step 1: Create a Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Give it a name (e.g., "StartPage Bot")
4. Select the workspace where you want to use it
5. Click **"Submit"**
6. Copy the **Internal Integration Token** - you'll need this for your `.env` file

### Step 2: Create Your Dashboard Page

1. In Notion, create a new page (this will be your daily dashboard)
2. Give it a title like "📊 Daily Dashboard" or "Morning Briefing"
3. Add a **Callout block** at the top - this will display your daily random fact
4. You can add any other static content you want (headers, dividers, etc.)

Your page structure should look like this:
```
📊 Daily Dashboard
├── 💡 [Callout Block] ← This will show the daily fact
└── [Daily updates will appear here]
```

### Step 3: Get Your Page ID and Block ID

**To get the Page ID:**
1. Click "Share" on your Notion page
2. Click "Copy link"
3. The URL will look like: `https://www.notion.so/Your-Page-Title-abc123def456...`
4. The Page ID is the part after the last dash: `abc123def456...`

**To get the Block ID (Callout):**
1. Hover over your callout block
2. Click the ⋮⋮ (six dots) icon
3. Click "Copy link to block"
4. The URL will look like: `https://www.notion.so/...#xyz789abc123...`
5. The Block ID is the part after the `#`: `xyz789abc123...`

**Important:** Remove any hyphens from both IDs. For example:
- ❌ `abc123-def456-ghi789`
- ✅ `abc123def456ghi789`

### Step 4: Share Page with Integration

1. Open your dashboard page in Notion
2. Click the **"..."** menu in the top right
3. Scroll down and click **"Add connections"**
4. Find and select your integration (e.g., "StartPage Bot")
5. Click **"Confirm"**

Now your integration has access to read and write to this page!

---

## Part 3: Gathering Environment Variables

Create a `.env` file in the project root with all necessary credentials:

```bash
# Notion Configuration
NOTION_TOKEN=secret_xxx...                    # From Step 2.1
PAGE_ID=abc123def456ghi789                    # From Step 2.3
BLOCK_ID=xyz789abc123def456                   # From Step 2.3

# Location Settings
CITY=London                                   # Or your preferred city
TIMEZONE=Europe/London                        # IANA timezone

# iCloud Calendar (for calendar events)
ICLOUD_USERNAME=your.email@icloud.com
ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx      # See below

# AWS Deployment (needed for `make deploy`)
S3_BUCKET=your-startpage-bucket              # S3 bucket for Lambda package
```

### Getting iCloud App-Specific Password

Apple requires app-specific passwords for third-party access:

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in with your Apple ID
3. In the **Security** section, find **App-Specific Passwords**
4. Click **"Generate an app-specific password"**
5. Enter a label (e.g., "StartPage Calendar")
6. Copy the generated password (format: `xxxx-xxxx-xxxx-xxxx`)
7. Paste it into your `.env` file as `ICLOUD_APP_PASSWORD`

**Note:** You only see this password once, so save it immediately!

### Configuration Checklist

Before proceeding, verify you have:
- ✅ Notion integration token
- ✅ Page ID (no hyphens)
- ✅ Block ID (no hyphens)
- ✅ City name for weather
- ✅ Your timezone
- ✅ iCloud username
- ✅ iCloud app-specific password
- ✅ S3 bucket name (for AWS deployment)

---

## Part 4: Testing Locally

Now let's make sure everything works before deploying to AWS.

### Step 1: Install Dependencies

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### Step 2: Run the Application

```bash
poetry run python -m startpage.startpage
```

You should see output like:
```
2026-02-09 10:30:45 - startpage.startpage - INFO - Starting StartPage application
2026-02-09 10:30:45 - startpage.startpage - INFO - Fetching data from all sources concurrently
2026-02-09 10:30:52 - startpage.startpage - INFO - All data fetched successfully, building Notion page
2026-02-09 10:30:52 - startpage.startpage - INFO - Appending new day section: Sunday 09 of February
2026-02-09 10:30:53 - startpage.startpage - INFO - Updating fact block
2026-02-09 10:30:53 - startpage.startpage - INFO - StartPage update completed successfully
```

### Step 3: Verify in Notion

Open your Notion page and you should see:
- A new header with today's date (e.g., "Sunday 09 of February")
- Weather information for your city
- Currency rates (₽ and $ based)
- Cryptocurrency prices
- Your calendar events for today
- 5 curated tech news articles
- Updated fact in the callout block

### Troubleshooting Common Issues

**"NOTION_TOKEN not set" error:**
- Ensure your `.env` file is in the project root
- Check that the token starts with `secret_`

**"Could not fetch weather" error:**
- Verify your `CITY` value is spelled correctly
- Try a major city nearby if your city isn't recognized

**"Calendar authentication failed" error:**
- Confirm your iCloud app-specific password is correct
- Make sure you're using your full iCloud email address

**No calendar events showing:**
- Check that you have events scheduled for today
- Verify the `TIMEZONE` setting matches your location

---

## Part 5: Deploying with CloudFormation

Now let's deploy StartPage to AWS Lambda so it runs automatically every day.

### Step 1: Install AWS CLI

**macOS:**
```bash
brew install awscli
```

**Linux/Windows:**
Follow the [official installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

**Verify installation:**
```bash
aws --version
```

### Step 2: Configure AWS Credentials

```bash
aws configure
```

You'll be prompted for:

- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Output format (just press Enter for default)

**Don't have AWS credentials?**

1. Log into [AWS Console](https://console.aws.amazon.com)
2. Go to IAM → Users
3. Click "Add users"
4. Enable "Programmatic access"
5. Attach "AdministratorAccess" policy (or create a custom policy)
6. Save the Access Key ID and Secret Access Key

### Step 3: Create an S3 Bucket

You need an S3 bucket to store the Lambda deployment package:

```bash
aws s3 mb s3://your-startpage-bucket --region us-east-1
```

### Step 4: Build and Upload the Lambda Package

```bash
# Install the Lambda build plugin (one-time setup)
poetry self add poetry-plugin-lambda-build

# Build the deployment package
poetry build-lambda

# Upload to S3
aws s3 cp package.zip s3://your-startpage-bucket/startpage/package.zip
```

### Step 5: Deploy with CloudFormation

The project includes a `template.yaml` that defines all AWS resources: Lambda function, IAM role, EventBridge schedule, and CloudWatch log group.

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

This creates the entire infrastructure in one command. CloudFormation will:

1. Create an IAM role with basic Lambda execution permissions
2. Deploy your Lambda function with the code from S3
3. Create an EventBridge rule to trigger the function daily
4. Set up CloudWatch log group with 7-day retention

**Alternatively**, if you have your `.env` file configured with all the variables (including `S3_BUCKET`), you can use the Makefile shortcut which handles building, uploading to S3, and deploying in one command:

```bash
make deploy
```

The process takes 2-3 minutes. When complete, you'll see:

```text
Successfully created/updated stack - startpage in us-east-1
```

### Step 6: Test Your Lambda Function

Invoke your function manually to verify it works:

```bash
aws lambda invoke \
  --function-name startpage \
  --invocation-type RequestResponse \
  --log-type Tail \
  output.json

# View the response
cat output.json
```

You should see:
```json
{
  "statusCode": 200,
  "body": "StartPage updated successfully"
}
```

Check your Notion page - you should see a new daily entry!

### Step 7: Monitor Execution

View your Lambda logs:

```bash
# See recent logs
aws logs tail /aws/lambda/startpage --since 1h

# Follow logs in real-time
aws logs tail /aws/lambda/startpage --follow
```

Or use the AWS Console:

1. Go to CloudWatch → Log groups
2. Find `/aws/lambda/startpage`
3. Browse execution logs

### Adjusting the Schedule

To run at a different time, redeploy with a new `ScheduleExpression`:

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name startpage \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides ScheduleExpression='cron(0 8 * * ? *)' ...
```

**Common schedules:**

- `cron(0 6 * * ? *)` - Daily at 6 AM UTC
- `cron(0 */6 * * ? *)` - Every 6 hours
- `cron(0 8 * * MON *)` - Every Monday at 8 AM UTC

**Note:** AWS EventBridge uses UTC time. Convert your local time to UTC for the schedule.

---

## Part 6: Automating Deployments with GitHub CI/CD

Now let's set up automatic deployments so every time you push changes to the `main` branch, your Lambda function updates automatically.

### Step 1: Fork the Repository

1. Go to [https://github.com/Driim/notion-startpage](https://github.com/Driim/notion-startpage)
2. Click the **"Fork"** button in the top right
3. Select your GitHub account as the destination
4. Wait for the fork to complete
5. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/notion-startpage.git
   cd notion-startpage
   ```

### Step 2: Create IAM User for GitHub Actions

Create a dedicated IAM user with permissions for S3 upload and CloudFormation deployment. See [AWS Lambda Setup Guide](AWS_LAMBDA_SETUP.md#get-aws-credentials-for-github-actions) for the full IAM policy.

Quick version:

```bash
# Create IAM user
aws iam create-user --user-name github-actions-startpage

# Attach AdministratorAccess for simplicity (or use the fine-grained policy from the setup guide)
aws iam attach-user-policy \
  --user-name github-actions-startpage \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create access key
aws iam create-access-key --user-name github-actions-startpage
```

Save the **AccessKeyId** and **SecretAccessKey** from the output!

### Step 3: Configure GitHub Secrets

1. Go to your forked repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Add these secrets one by one:

| Secret Name | Value | Example |
| ----------- | ----- | ------- |
| `AWS_ACCESS_KEY_ID` | From IAM user creation | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | From IAM user creation | `wJalrX...` |
| `AWS_REGION` | Your Lambda region | `us-east-1` |
| `S3_BUCKET` | S3 bucket for deployment package | `your-startpage-bucket` |
| `NOTION_TOKEN` | Notion API token | `secret_xxx` |
| `PAGE_ID` | Notion page ID | `abc123def456` |
| `BLOCK_ID` | Notion block ID | `xyz789abc123` |
| `CITY` | City for weather | `London` |
| `ICLOUD_USERNAME` | iCloud email | `you@icloud.com` |
| `ICLOUD_APP_PASSWORD` | iCloud app password | `xxxx-xxxx-xxxx-xxxx` |
| `TIMEZONE` | IANA timezone | `Europe/London` |

**To add each secret:**
1. Click "New repository secret"
2. Enter the **Name**
3. Paste the **Value**
4. Click "Add secret"

### Step 4: Understanding the Workflow

The GitHub Actions workflow (`.github/workflows/deploy-lambda.yml`) runs when:
- A pull request is **merged** into the `main` branch

It performs these steps:

1. ✅ Checks out the code
2. ✅ Sets up Python 3.12
3. ✅ Installs Poetry and the Lambda build plugin
4. ✅ Builds a Lambda-compatible deployment package
5. ✅ Uploads `package.zip` to S3 with an MD5 hash suffix for versioning (e.g., `package-a1b2c3d4.zip`)
6. ✅ Deploys the CloudFormation stack (creates/updates Lambda, EventBridge, IAM role)

### Step 5: Test the CI/CD Pipeline

Let's make a small change to trigger the workflow:

```bash
# Create a new branch
git checkout -b test-deployment

# Make a small change (e.g., update README)
echo "\n## My Personal StartPage\n" >> README.md

# Commit and push
git add README.md
git commit -m "Test CI/CD deployment"
git push origin test-deployment
```

Now on GitHub:
1. Go to your repository
2. Click **"Pull requests"** → **"New pull request"**
3. Select `test-deployment` branch
4. Click **"Create pull request"**
5. Add a title like "Test deployment"
6. Click **"Create pull request"**
7. Click **"Merge pull request"**
8. Click **"Confirm merge"**

Watch the magic happen:
1. Go to **Actions** tab
2. You'll see a workflow running
3. Click on it to watch the deployment in real-time
4. After 2-3 minutes, it should complete successfully ✅

Verify the deployment:
```bash
# Invoke your Lambda function
aws lambda invoke \
  --function-name startpage \
  --log-type Tail \
  output.json

# Check the response
cat output.json
```

### Step 6: Making Updates

From now on, whenever you want to update your StartPage:

1. **Make changes locally:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b my-feature
   # Make your changes...
   ```

2. **Test locally:**
   ```bash
   poetry run python run.py
   ```

3. **Create pull request:**
   ```bash
   git add .
   git commit -m "Add new RSS feed"
   git push origin my-feature
   # Create PR on GitHub
   ```

4. **Merge to main:**
   - Once merged, GitHub Actions automatically deploys to Lambda!

### Common Workflow Scenarios

**Update RSS feeds:**
Edit `src/startpage/startpage.py`, modify the `feeds` list, create a PR, merge.

**Change schedule:**
Update the `ScheduleExpression` parameter in the CloudFormation deploy step in `.github/workflows/deploy-lambda.yml`, create a PR, merge. For local deployments, you can also pass a custom schedule via `make deploy` or directly to `aws cloudformation deploy`.

**Update Python version:**
Edit both `.github/workflows/deploy-lambda.yml` and `template.yaml`, create a PR, merge.

---

## Conclusion

Congratulations! You've built a fully automated Notion dashboard that:
- ✅ Runs daily on AWS Lambda (serverless, $0/month)
- ✅ Aggregates data from multiple sources concurrently
- ✅ Updates your Notion page automatically
- ✅ Deploys automatically via GitHub Actions
- ✅ Requires zero maintenance

### What's Next?

**Customize your data sources:**
- Add more RSS feeds in `src/startpage/startpage.py`
- Integrate new APIs (GitHub activity, Spotify stats, etc.)
- Customize the Notion block formatting

**Enhance the dashboard:**
- Add graphs and charts using Notion's embed blocks
- Create separate pages for different data categories
- Archive old entries automatically

**Improve reliability:**
- Set up CloudWatch alarms for failures
- Add SNS notifications for errors
- Implement retry logic for API calls

**Security improvements:**
- Use AWS Secrets Manager instead of environment variables
- Enable VPC for Lambda if accessing private resources
- Set up AWS X-Ray for distributed tracing

### Cost Breakdown

With the default daily schedule:
- **Lambda:** 30 executions/month × 15 seconds = 7.5 minutes/month ✅ FREE (1M requests, 400K GB-seconds free)
- **EventBridge:** 30 invocations/month ✅ FREE (< 1M invocations)
- **CloudWatch Logs:** ~50 MB/month ✅ FREE (5 GB ingestion, 7-day retention)
- **S3 (deployment package):** < 50 MB ✅ FREE (5 GB storage)

**Total monthly cost: $0.00** 🎉

### Resources

- [GitHub Repository](https://github.com/Driim/notion-startpage)
- [Notion API Documentation](https://developers.notion.com)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)

### Share Your Dashboard

I'd love to see what you build! Share your customized StartPage:
- Tweet your dashboard [@YourTwitter](https://twitter.com)
- Open an issue with your modifications
- Submit a PR with new features

Happy automating! 🚀

---

*This project is open source under the MIT License. Contributions are welcome!*

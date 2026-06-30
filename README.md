# zacharygeorgebaker_backend

Dockerized Flask backend for [zacharygeorgebaker.com](https://www.zacharygeorgebaker.com).

- **Frontend repository:** [github.com/zgbaker54/zacharygeorgebaker](https://github.com/zgbaker54/zacharygeorgebaker)
- **Backend repository (you are here):** [github.com/zgbaker54/zacharygeorgebaker_backend](https://github.com/zgbaker54/zacharygeorgebaker_backend)

The backend is built with Flask and deployed on Railway. It provides API endpoints consumed by the frontend.

## Table of Contents

- [Local development setup](#local-development-setup)
- [Install venv for development](#install-venv-for-development)
- [Run the backend locally](#run-the-backend-locally)
- [Running tests](#running-tests)
- [Build and run with Docker](#build-and-run-with-docker)
- [Deploying to Railway](#deploying-to-railway)
- [Adding words to the 7Letters game database](#adding-words-to-the-7letters-game-database)
- [Infrastructure (Terraform)](#infrastructure-terraform)


## Local development setup

The app reads a few environment variables from a `.env` file at startup. Create a `.env` file in the project root with the following values to get started:

```env
AWS_ACCESS_KEY_ID=*****
AWS_SECRET_ACCESS_KEY=*****
AWS_DEFAULT_REGION=us-west-1
CORS_ORIGINS=http://localhost:5173,http://192.168.4.98:5173,https://www.zacharygeorgebaker.com
```

> **Note:**
> - `CORS_ORIGINS` is required and must be a comma-separated list of allowed frontend origins. If missing, the app will crash on startup.
> - The app also makes calls to DynamoDB to fetch the word of the day, landing bio, and resume link. To obtain valid credentials:
> 1. Go to the [AWS IAM Console](https://console.aws.amazon.com/iam/) → **Users** → click your username → **Security credentials** tab.
> 2. Under **Access keys**, click **Create access key**.
> 3. Choose **Application running outside AWS** and follow the prompts.
> 4. Copy the **Access key ID** and **Secret access key** into your `.env` file.
> 5. Ensure the IAM user has read access to the `ZacharyGeorgeBaker-Assets` and `ZacharyGeorgeBaker-7Letters` DynamoDB tables.

## Install venv for development

(You can get brew <a href=https://brew.sh>here</a>)

```
brew install python@3.11
```

Install venv and dependencies:
```
python3.14 -m venv ./venv;
source venv/bin/activate;
pip install -r requirements.txt;
pip install --upgrade pip;
```

## Run the backend locally

To run the Flask backend on your local machine for development and testing:

```
python app.py;
```

This starts the Flask development server on `http://localhost:8000`. The server will reload automatically when you make changes to `app.py`.

You can test the available routes using [Bruno](https://www.usebruno.com/).

## Running tests

Unit tests live in the `tests/` directory and run with [pytest](https://docs.pytest.org/).

`pytest` is a development-only dependency and is not part of `requirements.txt` (which is the production/Docker manifest). Install it into your virtual environment if you haven't already:

```
source venv/bin/activate;
pip install pytest;
```

Run the full test suite from the project root:

```
pytest
```

Useful variations:

```
pytest -v                                   # verbose, one line per test
pytest tests/test_annotate_letters.py       # run a single test file
pytest -k annotate                          # run tests matching a keyword
```

> **Note:** Run pytest from the project root so the `src` package imports correctly. A root-level `conftest.py` adds the project root to `sys.path` to make this reliable.

## Build and run with Docker

To build and run the API locally using Docker:

### Build the Docker image

```
docker build -t zacharygeorgebaker-backend .
```

### Run the container

```
docker run -p 8000:8000 -e PORT=8000 zacharygeorgebaker-backend
```

This starts a Gunicorn server inside the container, accessible at `http://localhost:8000`.

### Test the API

Once the container is running, you can test it with `curl`:

```
curl http://localhost:8000/ping
```

Or use [Bruno](https://www.usebruno.com/) to test the available routes.

## Deploying to Railway

The API is deployed on Railway at the following URLs:

- **Project URL:** [https://railway.com/project/a756962e-ad7e-4d7b-b0e3-8ecb132d2f3e](https://railway.com/project/a756962e-ad7e-4d7b-b0e3-8ecb132d2f3e)
- **API Domain URL:** [https://zacharygeorgebakerbackend-production.up.railway.app](https://zacharygeorgebakerbackend-production.up.railway.app)

You can test the API endpoints using the deployed URL:

```
curl https://zacharygeorgebakerbackend-production.up.railway.app/ping
```

## Adding words to the 7Letters game database

The 7Letters word-of-the-day game uses two scripts in the `word-management/` directory to manage its word list in DynamoDB.

### Prerequisites

Ensure you have AWS credentials configured (see [Local development setup](#local-development-setup)) and the required Python dependencies:

```bash
# Activate your virtual environment
source venv/bin/activate

# Install additional dependencies for word management
pip install pandas numpy boto3
```

### 1. Select words (`wordSelection.py`)

This script presents 7-letter words from `wordList.txt` one at a time for interactive approval.

```bash
cd word-management/
python wordSelection.py
```

**How it works:**
- Reads all words from `wordList.txt` and filters to 7-letter words
- Shuffles them randomly and saves the shuffled list to `wordList7Letters.txt`
- Presents each word for manual review
- Skips words already in `wordListAccepted.txt`

**Controls:**
- Press **y** to accept a word (appended to `wordListAccepted.txt`)
- Press **n** to reject it
- Press **q** to quit early

### 2. Upload words (`wordUpload.py`)

This script reads the accepted words from `wordListAccepted.txt` and uploads them to the `ZacharyGeorgeBaker-7Letters` DynamoDB table.

```bash
cd word-management/
python wordUpload.py
```

When prompted, you'll be asked to configure two settings:

1. **Start date** — choose when to begin assigning dates:
   - `today` — uses the current date
   - `tomorrow` — uses the next calendar day
   - `YYYY-MM-DD` — enter a custom date (e.g. `2026-07-01`)

2. **Skip existing dates mode** — choose how to handle dates that already have words:
   - `y` (yes) — if a date already has a word, skip to the next available date
   - `n` (no) — use sequential dates starting from your chosen date (original behavior)

**How it works:**
- Queries the existing DynamoDB table to check for duplicate words and existing dates
- Reads words from `wordListAccepted.txt`
- Assigns each word a date based on your chosen mode:
  - **Skip mode disabled:** Sequential dates starting from your chosen date
  - **Skip mode enabled:** Finds the next available date that doesn't already have a word
- Uploads each word with the following schema:

| Field          | Type   | Description                                      |
|----------------|--------|--------------------------------------------------|
| `WordOfTheDay` | String | Partition key, always set to `"WordOfTheDay"`    |
| `Date`         | String | Date in `YYYY-MM-DD` format, one per word        |
| `Word`         | String | The 7-letter word                                |

The script skips words already in the database and raises an error if any duplicates are found in the existing data. When skip mode is enabled, it will also display messages when dates are being skipped due to existing words.

### File structure

```
word-management/
├── wordList.txt           # Master list of all words
├── wordList7Letters.txt   # Shuffled 7-letter words (generated by wordSelection.py)
├── wordListAccepted.txt   # Manually approved words (generated by wordSelection.py)
├── wordSelection.py       # Interactive word approval script
└── wordUpload.py          # DynamoDB upload script
```

## Infrastructure (Terraform)

The backend's AWS infrastructure (Lambda, EventBridge, SNS, DynamoDB) is managed as code with Terraform. All resources are defined in `infra/main.tf`.

### What's managed

| Resource                          | Description                                                      |
|-----------------------------------|------------------------------------------------------------------|
| `aws_s3_bucket.tf_state`          | S3 bucket storing the Terraform state file                       |
| `aws_s3_bucket_versioning`        | Versioning enabled on the state bucket for recovery              |
| `aws_iam_role.lambda_exec_role`   | IAM role assumed by the Lambda function                          |
| `aws_iam_role_policy.lambda_policy` | IAM policy granting Lambda access to CloudWatch Logs, DynamoDB, and SNS |
| `aws_lambda_function.date_checker` | Daily Lambda that verifies tomorrow's word exists in DynamoDB   |
| `aws_cloudwatch_event_rule.daily_cron` | EventBridge rule triggering the Lambda at midnight UTC      |
| `aws_cloudwatch_event_target.trigger_lambda` | Connects the EventBridge rule to the Lambda          |
| `aws_lambda_permission.allow_eventbridge` | Grants EventBridge permission to invoke the Lambda       |
| `aws_sns_topic.word_alerts`       | SNS topic for alert notifications                                |
| `aws_sns_topic_subscription.email_sub` | Email subscription sending alerts to zgbaker54@gmail.com    |
| `aws_dynamodb_table.seven_letters_table` | DynamoDB table storing 7-letter words for the game        |

### First-time setup

```bash
# Install Terraform
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# (Optional) Add an alias to your .zshrc
alias tf="terraform"

# Verify installation
tf -v

# Initialize Terraform (downloads providers, sets up the S3 backend)
cd infra/
tf init
```

> **Note:** The S3 backend bucket (`zacharygeorgebaker-tf-state-storage`) must already exist before running `tf init`. If it doesn't, create it manually first.

### Updating infrastructure

1. **Edit `infra/main.tf`** — add, modify, or remove resources as needed.

2. **Preview changes** — see what Terraform will create, update, or destroy:
   ```bash
   cd infra/
   tf plan
   ```
   Review the output carefully. Resources marked with a red `-` (minus) will be **destroyed**.

3. **Apply changes** — deploy the changes to AWS:
   ```bash
   tf apply
   ```
   Terraform will show the plan again and prompt for confirmation. Type `yes` to proceed.

### State management

Terraform state is stored remotely in the S3 bucket `zacharygeorgebaker-tf-state-storage` (key: `backend/terraform.tfstate`), with server-side encryption enabled. This allows the state to be shared across team members and CI/CD pipelines.

- **Do not delete or manually edit the state file** — it can corrupt Terraform's understanding of your infrastructure.
- If you need to inspect state, use `tf state list` or `tf state show <resource>`.

# set up terraform
terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 5.0"
        }
    }
    # allows s3 to track tf state instead of this being stored locally
    backend "s3" {
        bucket = "zacharygeorgebaker-tf-state-storage"
        key = "backend/terraform.tfstate"
        region = "us-west-1"
        encrypt = true
    }
}

# local values to be referenced
locals {
    tf_state_bucket_name = "zacharygeorgebaker-tf-state-storage"
    region = "us-west-1"
}

# provider
provider "aws" {
    region = local.region
}

# allows tf state to be stored in S3 instead of locally untracked
resource "aws_s3_bucket" "tf_state" {
    bucket = local.tf_state_bucket_name
}
resource "aws_s3_bucket_versioning" "state_versioning" {
    bucket = aws_s3_bucket.tf_state.id
    versioning_configuration {
        status = "Enabled"
    }
}

# --------------------------------------------------------------------------------
# LAMBDA -------------------------------------------------------------------------

# lambda function's script
data "archive_file" "lambda_zip" {
    type = "zip"
    source_file = "${path.module}/../src/utils/check_tomorrows_word.py"
    output_path = "${path.module}/check_tomorrows_word.zip"
}

# lambda role
resource "aws_iam_role" "lambda_exec_role" {
    name = "zgb_lambda_execution_role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = { Service = "lambda.amazonaws.com" }
        }]
    })
}

# lambda policy
resource "aws_iam_role_policy" "lambda_policy" {
    name = "zgb_lambda_execution_role"
    role = aws_iam_role.lambda_exec_role.id
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
                Resource = "arn:aws:logs:*:*:*"
            },
            {
                Effect = "Allow"
                Action   = ["dynamodb:Scan", "dynamodb:Query"]
                Resource = "arn:aws:dynamodb:*:*:table/ZacharyGeorgeBaker-7Letters"
            },
            {
                Effect = "Allow"
                Action   = ["sns:Publish"]
                Resource = aws_sns_topic.word_alerts.arn
            },
        ]
    })
}

# lambda function
resource "aws_lambda_function" "date_checker" {
    filename = data.archive_file.lambda_zip.output_path
    function_name = "zgb_daily_date_checker"
    role = aws_iam_role.lambda_exec_role.arn
    handler = "check_tomorrows_word.lambda_handler"
    runtime = "python3.13"
    source_code_hash = data.archive_file.lambda_zip.output_base64sha256
    environment {
        variables = {
            SNS_TOPIC_ARN = aws_sns_topic.word_alerts.arn
            DB_TABLE_NAME = aws_dynamodb_table.seven_letters_table.name
        }
    }
}

# --------------------------------------------------------------------------------
# EVENTBRIDGE --------------------------------------------------------------------

# cron trigger to once once per day at midnight UTC
resource "aws_cloudwatch_event_rule" "daily_cron" {
    name = "zgb-daily-date-check"
    description = "Triggers Lambda function daily to verify tomorrow's data exists."
    schedule_expression = "cron(0 0 * * ? *)"
}

# lambda trigger
resource "aws_cloudwatch_event_target" "trigger_lambda" {
    rule = aws_cloudwatch_event_rule.daily_cron.name
    target_id = "TriggerCheckerLambda"
    arn = aws_lambda_function.date_checker.arn
}

# permission for EventBridge to invoke the lambda
resource "aws_lambda_permission" "allow_eventbridge" {
    statement_id = "AllowExecutionFromEventBridge"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.date_checker.function_name
    principal = "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.daily_cron.arn
}

# --------------------------------------------------------------------------------
# SNS ----------------------------------------------------------------------------

# sns
resource "aws_sns_topic" "word_alerts" {
    name = "zgb_dynamodb-daily-word-alerts"
}

# where sns sends it's notifications to
resource "aws_sns_topic_subscription" "email_sub" {
    topic_arn = aws_sns_topic.word_alerts.arn
    protocol = "email"
    endpoint = "zgbaker54@gmail.com"
}

# --------------------------------------------------------------------------------
# DYNAMODB -----------------------------------------------------------------------

resource "aws_dynamodb_table" "seven_letters_table" {
    name = "ZacharyGeorgeBaker-7Letters"
    billing_mode = "PAY_PER_REQUEST"
    hash_key = "WordOfTheDay"
    range_key = "Date"
    attribute {
        name = "WordOfTheDay"
        type = "S"
    }
    attribute {
        name = "Date"
        type = "S"
    }
}

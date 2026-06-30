import os
import boto3
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError

# Initialize AWS clients outside the handler for connection re-use
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

DB_TABLE_NAME = os.environ['DB_TABLE_NAME']
# Pulling the SNS Topic ARN dynamically from the Terraform Environment Variable
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

table = dynamodb.Table(DB_TABLE_NAME)

def lambda_handler(event, context):
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"Checking for data matching tomorrow's date: {tomorrow}")

    try:
        response = table.query(
            KeyConditionExpression='#pk = :pk_val AND #sk = :tomorrow_val',
            ExpressionAttributeNames={
                '#pk': 'WordOfTheDay', # Your Partition Key attribute name
                '#sk': 'Date'          # Your Sort Key attribute name (capital D)
            },
            ExpressionAttributeValues={
                ':pk_val': 'WordOfTheDay', # The literal string value used for every row
                ':tomorrow_val': tomorrow   # Tomorrow's date string (e.g., "2026-07-01")
            }
        )

        items = response.get('Items', [])

        if items:
            word_found = items[0].get('Word', 'Unknown Word')
            print(f"Success! Found data for tomorrow ({tomorrow}). Word: '{word_found}'")
            return {
                'statusCode': 200,
                'body': f"Data exists for tomorrow. Found word: {word_found}"
            }
        else:
            print(f"Alert: No data found for tomorrow ({tomorrow})! Sending email...")

            message_body = (
                f"🚨 DYNAMODB ALERT 🚨\n\n"
                f"The daily check completed, and NO data was found for tomorrow: {tomorrow}.\n"
                f"Please log in and add a 7-letter word to the table '{DB_TABLE_NAME}' immediately."
            )

            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"Missing DynamoDB Data Alert - {tomorrow}",
                Message=message_body
            )

            return {
                'statusCode': 404,
                'body': "No data found for tomorrow. Email alert sent."
            }

    except ClientError as e:
        print(f"Error scanning DynamoDB: {e.response['Error']['Message']}")
        return {
            'statusCode': 500,
            'body': "Internal server error scanning table."
        }
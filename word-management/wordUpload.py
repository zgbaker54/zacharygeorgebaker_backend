import boto3
from boto3.dynamodb.conditions import Key
import pandas as pd
from datetime import datetime, timedelta


# Prompt user for start date
while True:
    choice = input("Start date? (today / tomorrow / YYYY-MM-DD): ").strip().lower()
    if choice == 'today':
        start_date = datetime.now().date()
        break
    elif choice == 'tomorrow':
        start_date = datetime.now().date() + timedelta(days=1)
        break
    else:
        try:
            start_date = datetime.strptime(choice, '%Y-%m-%d').date()
            break
        except ValueError:
            print("Invalid input. Enter 'today', 'tomorrow', or a date in YYYY-MM-DD format.")

print(f"Using start date: {start_date}")

# Prompt user for skip mode
while True:
    skip_mode = input("Skip to next date if word exists for proposed date? (y/n): ").strip().lower()
    if skip_mode in ['y', 'yes']:
        skip_existing_dates = True
        break
    elif skip_mode in ['n', 'no']:
        skip_existing_dates = False
        break
    else:
        print("Invalid input. Enter 'y' for yes or 'n' for no.")

print(f"Skip existing dates mode: {'Enabled' if skip_existing_dates else 'Disabled'}")

db_resource = boto3.Session().resource('dynamodb', region_name='us-west-1')
db_table = db_resource.Table('ZacharyGeorgeBaker-7Letters')
resp = db_table.query(
    KeyConditionExpression=Key('WordOfTheDay').eq('WordOfTheDay'),
    ScanIndexForward=False,
)
print(resp)

allWords = set()
existingDates = set()
for item in resp['Items']:
    word = item['Word']
    date = item['Date']
    if word in allWords:
        raise AssertionError(f"DB Error! Duplicate word found: {word}")
    allWords.add(word)
    existingDates.add(date)

acceptedWords = pd.read_csv('wordListAccepted.txt', sep=r'\n', engine='python', header=None, names=['Words'])

print(acceptedWords)
i = 0
for acceptedWord in acceptedWords.to_numpy():
    word = acceptedWord[0]
    if word in allWords:
        print(f"Skipping '{word}' — already in database")
        continue

    # Find the next available date
    while True:
        date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')

        if skip_existing_dates and date in existingDates:
            print(f"Date {date} already has a word, skipping to next date")
            i += 1
            continue
        else:
            break

    print(f"{word} -> {date}")
    db_table.put_item(
        Item={
            'WordOfTheDay': 'WordOfTheDay',
            'Date': date,
            'Word': word,
        }
    )

    # Add the new date to existing dates to avoid conflicts in subsequent iterations
    existingDates.add(date)
    i += 1

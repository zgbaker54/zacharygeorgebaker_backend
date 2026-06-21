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

db_resource = boto3.Session().resource('dynamodb', region_name='us-west-1')
db_table = db_resource.Table('ZacharyGeorgeBaker-7Letters')
resp = db_table.query(
    KeyConditionExpression=Key('WordOfTheDay').eq('WordOfTheDay'),
    ScanIndexForward=False,
)
print(resp)

allWords = set()
for item in resp['Items']:
    word = item['Word']
    if word in allWords:
        raise AssertionError(f"DB Error! Duplicate word found: {word}")
    allWords.add(word)

acceptedWords = pd.read_csv('wordListAccepted.txt', sep=r'\n', engine='python', header=None, names=['Words'])

print(acceptedWords)
i = 0
for acceptedWord in acceptedWords.to_numpy():
    word = acceptedWord[0]
    if word in allWords:
        print(f"Skipping '{word}' — already in database")
        continue
    date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
    print(f"{word} -> {date}")
    db_table.put_item(
        Item={
            'WordOfTheDay': 'WordOfTheDay',
            'Date': date,
            'Word': word,
        }
    )
    i += 1

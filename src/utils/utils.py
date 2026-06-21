import boto3
from datetime import datetime


# load all valid 7-letter words into a set for fast lookups
_VALID_7_LETTER_WORDS: set[str] = set()
try:
    with open('wordList7Letters.txt', 'r') as f:
        for line in f:
            word = line.strip()
            if word:
                _VALID_7_LETTER_WORDS.add(word)
except FileNotFoundError:
    pass  # file not present in all environments (e.g. Lambda)


# get the corresponding `AssetValue` based on the `AssetName` key from the dynamoDB database table named `ZacharyGeorgeBaker-Assets`
def GetValueFromDb(key: str) -> str:
    value = ""
    try:
        db_resource = boto3.Session().resource('dynamodb', region_name='us-west-1')
        db_table = db_resource.Table('ZacharyGeorgeBaker-Assets')
        resp = db_table.get_item(
            Key={
                'AssetName': key
            }
        )
        if 'Item' in resp:
            value = resp['Item']['AssetValue']
        print(resp)
    finally:
        pass
    return value


# check if a word is a valid 7-letter word
def IsValidWord(word: str) -> bool:
    return word in _VALID_7_LETTER_WORDS


# get today's word and date from the ZacharyGeorgeBaker-7Letters table
def GetWordOfTheDay() -> dict:
    result = {"word": "", "date": ""}
    try:
        db_resource = boto3.Session().resource('dynamodb', region_name='us-west-1')
        db_table = db_resource.Table('ZacharyGeorgeBaker-7Letters')
        today = datetime.now().strftime('%Y-%m-%d')
        resp = db_table.get_item(
            Key={
                'WordOfTheDay': 'WordOfTheDay',
                'Date': today,
            }
        )
        if 'Item' in resp:
            result["word"] = resp['Item']['Word']
            result["date"] = resp['Item']['Date']
        print(resp)
    finally:
        pass
    return result

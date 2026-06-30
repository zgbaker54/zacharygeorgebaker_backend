import boto3
from datetime import datetime
import copy
import os


# load all valid 7-letter words into a set for fast lookups
_VALID_7_LETTER_WORDS: set[str] = set()

def _load_word_list():
    """Load the 7-letter word list from file, trying multiple possible paths."""
    possible_paths = [
        'wordList7Letters.txt',  # deployed environment (copied to root)
        'word-management/wordList7Letters.txt',  # local development
        os.path.join(os.path.dirname(__file__), '../../word-management/wordList7Letters.txt'),  # relative to utils.py
    ]
    for path in possible_paths:
        try:
            with open(path, 'r') as f:
                words_loaded = 0
                for line in f:
                    word = line.strip()
                    if word:
                        _VALID_7_LETTER_WORDS.add(word)
                        words_loaded += 1
                print(f"Successfully loaded {words_loaded} words from {path}")
                return
        except FileNotFoundError:
            continue
    # If we get here, none of the paths worked
    raise FileNotFoundError(
        f"Could not find wordList7Letters.txt in any of the expected locations: {possible_paths}"
    )

# Load the word list at module import time
_load_word_list()


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
    except Exception:
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
    except Exception:
        pass
    return result

# annotate each guess in the provided guess sequence against today's word of the day;
# returns the updated guess sequence and an optional snackbar message for invalid words
def AnnotateGuessSequence(guessSequence: dict) -> tuple[dict, str]:
    snackbarMessage = ""
    wotdResp = GetWordOfTheDay()
    date = wotdResp["date"]
    answer = wotdResp["word"].upper()
    if len(answer) == 0:
        raise AssertionError("No word of the day available")
    if guessSequence['date'] != date:
        raise AssertionError("Date mismatch during guess annotation")
    for guess in guessSequence['guesses']:
        guessWord = "".join(map(lambda guessLetter: guessLetter['letter'], guess['letters']))
        if guess['submitted'] and guess['validWord'] is None:
            if IsValidWord(guessWord.lower()):
                guess['validWord'] = True
                # annotate letters
                guess['letters'] = annotateLetters(copy.deepcopy(guess['letters']), answer)
            else:
                guess['submitted'] = False
                snackbarMessage = f"Invalid word: {guessWord.upper()}"
    return (guessSequence, snackbarMessage)

# evaluate each letter in a single guess against the answer and set the letter's
# 'evaluation' field to 'exact', 'misplaced', or 'wrong'
def annotateLetters(guessLetters, answerStr: str):
    for (idx, guessLetter) in enumerate(guessLetters):  # capitalize all letters
        guessLetters[idx]['letter'] = guessLetters[idx]['letter'].upper()
    answer = list(answerStr)
    exactIndexes = []
    for (idx, guessLetter) in enumerate(guessLetters):
        if guessLetter['letter'] == answer[idx]:
            guessLetters[idx]['evaluation'] = 'exact'
            exactIndexes.append(idx)
    for (idx, _) in enumerate(answer):
        if idx in exactIndexes:
            answer[idx] = ''
    for (idx, guessLetter) in enumerate(guessLetters):
        if idx in exactIndexes:
            continue
        if guessLetter['letter'] in answer:
            guessLetter['evaluation'] = 'misplaced'
            # consume the matched occurrence so a repeated guess letter can't be
            # marked 'misplaced' more times than the letter appears in the answer
            answer[answer.index(guessLetter['letter'])] = ''
        else:
            guessLetter['evaluation'] = 'wrong'
    return guessLetters

# zacharygeorgebaker_backend
Dockerized Flask backend for zacharygeorgebaker.com using AWS ECR, Lambda, and API Gateway.

## Table of Contents

- [Install venv for development](#install-venv-for-development)
- [Run the backend locally](#run-the-backend-locally)
- [Build and run with Docker](#build-and-run-with-docker)
- [Deploying to Railway](#deploying-to-railway)
- [Adding words to the 7Letters game database](#adding-words-to-the-7letters-game-database)


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

The 7Letters word-of-the-day game uses two scripts to manage its word list in DynamoDB.

### 1. Select words (`wordSelection.py`)

This script presents 7-letter words from `wordList.txt` one at a time for interactive approval.

```
python wordSelection.py
```

- Press **y** to accept a word (appended to `wordListAccepted.txt`)
- Press **n** to reject it
- Press **q** to quit early
- Already-accepted words are skipped automatically

### 2. Upload words (`wordUpload.py`)

This script reads the accepted words from `wordListAccepted.txt` and uploads them to the `ZacharyGeorgeBaker-7Letters` DynamoDB table.

```
python wordUpload.py
```

When prompted, choose a start date:

- `today` — uses the current date
- `tomorrow` — uses the next calendar day
- `YYYY-MM-DD` — enter a custom date (e.g. `2026-07-01`)

Each word is assigned a sequential date starting from the chosen date, and uploaded with these fields:

| Field          | Type   | Description                                      |
|----------------|--------|--------------------------------------------------|
| `WordOfTheDay` | String | Partition key, always set to `"WordOfTheDay"`    |
| `Date`         | String | Date in `YYYY-MM-DD` format, one per word        |
| `Word`         | String | The 7-letter word                                |

The script also checks for duplicate words already in the table and raises an error if any are found.
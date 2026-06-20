# zacharygeorgebaker_backend
Dockerized Flask backend for zacharygeorgebaker.com using AWS ECR, Lambda, and API Gateway.

## Table of Contents

- [Install venv for development](#install-venv-for-development)
- [Run the backend locally](#run-the-backend-locally)
- [Build and run with Docker](#build-and-run-with-docker)


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

## Deploying to AWS
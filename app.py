import json
from flask import Flask, Response, request
from flask_cors import CORS
import serverless_wsgi
from src.utils.utils import GetValueFromDb
from src.regfigs import generate_regfig
from dotenv import load_dotenv


# load env vars from a .env file if present
load_dotenv()

# flask
app = Flask(__name__)

# Allow your specific frontend domains to make API calls
CORS(app, origins=[
    "http://localhost:5173",
    "https://zacharygeorgebaker.com"
])

# ------------------------------------------------------------------------------------------------------------------------------------------------
# test route (GET)
@app.route('/testGet', methods=['GET'])
def testGet():
    print("testGet")
    response = Response(
        json.dumps({"test": "testGet"}),
        status=201,
        content_type="application/json",
    )
    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# keep alive route (GET)
@app.route('/ping', methods=['GET'])
def ping():
    print("ping")
    response = Response(
        json.dumps({"status": "ok"}),
        status=200,
        content_type="application/json",
    )
    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# test route (POST)
@app.route('/testPost', methods=['POST'])
def testPost():
    print("testPost")
    response = Response(
        json.dumps({"test": "testPost", "body": request.json}),
        status=201,
        content_type="application/json",
    )
    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# route to generate regression sample figures based on the payload posted;
# uploads figures as png files to the zacharygeorgebaker-regfigs S3 bucket and then returns a signed url for the figure
@app.route('/regfigs', methods=['POST'])
def regfigs():
    print('regfigs method called')
    payload = request.json
    print(f"payload: {payload}")
    signed_url = generate_regfig(payload)
    print(f'regfigs method returning signed_url: {signed_url}')
    response = Response(
        json.dumps({'signed_url': signed_url}),
        status=200,
        content_type="application/json",
    )
    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# route to get the landing bio from the dynamoDB database
@app.route('/getLandingBio', methods=['GET'])
def getLandingBio():
    print('getLandingBio called')
    response = Response(
        json.dumps({"landingBio": GetValueFromDb("LandingBio")}),
        status=200,
        content_type="application/json",
    )
    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# route to get the resume link from the dynamoDB database
@app.route('/getResumeLink', methods=['GET'])
def getResumeLink():
    print('getResumeLink called')
    response = Response(
        json.dumps({"resumeLink": GetValueFromDb("ResumeLink")}),
        status=200,
        content_type="application/json",
    )
    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# handler function to accomodate Dockerized Flask Application - see Dockerfile: CMD [ "app.handler" ]
def handler(event, context):
    print(f"event: {event}")
    print(f"context: {context}")
    return serverless_wsgi.handle_request(app, event, context)

# ------------------------------------------------------------------------------------------------------------------------------------------------
# run this script to run the flask app on a local server
if __name__ == "__main__":
    app.run(port=8000, debug=True)
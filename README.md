# zacharygeorgebaker_backend
Dockerized Flask backend for zacharygeorgebaker.com using AWS ECR, Lambda, and API Gateway.

<br/>

## Install venv for development

(You can get brew <a href=https://brew.sh>here</a>)

```
brew install python@3.11
```

Install venv and dependencies:
```
python3.11 -m venv ./venv;
source venv/bin/activate;
pip install -r requirements.txt;
pip install --upgrade pip;
```

For local development you should also install `tensorflow-metal`. This dependency allows M1 macs to use their GPUs during TensorFlow model training. However, it cannot be dockerized so it needs to be omitted from `requirements.txt`.
```
pip install tensorflow-metal;
```

<br/>

## Creating this backend
These steps document my eventual solution in getting Flask, Docker, ECR, Lambda, and API Gateway working together.

<br/>

### Write a serverless flask app in python

Write a flask app in `app.py`. Ensure that the application includes the `handler(event, context)` function that uses `serverless_wsgi.handle_request(app, event, context)` (where `app` is the flask app object).

Also, due to Lambda proxy integration the backend's responses should support CORS for local development. In short, all routes should include the following in their response headers:
```
{
    "Access-Control-Allow-Headers" : "Content-Type",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}
```
See <a href=https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html#apigateway-enable-cors-proxy>this source here</a> for more details.

<br/>

### Building the Docker image pointed at the `handler` function in `app.py` and pushing to ECR

See `Dockerfile` for complete code. `FROM public.ecr.aws/lambda/python:3.11` uses a python build made for lambda. `CMD [ "app.handler" ]` points Containers to run the `handler` function in `app.py`, which in turn handles API Gateway requests and funnels them to the appropriate routes in the flask app.

Run `deployDocker.py` to get a set of commands to build a Docker image and push it to AWS ECR. Example lines are shown below (but do not use these - `deployDocker.py` generates these for you):


The following line builds the Docker container named `zacharygeorgebaker_backend` and tags it as `v1.0.0`:
```
docker build -t zacharygeorgebaker_backend:v1.0.0 .
```

Tags (e.g. `v1.0.0`) need to be unique - check Docker (desktop) to see and delete already-existing builds.

Further example lines for pushing to ECR - the following code pushes the Docker image named `zacharygeorgebaker_backend` (tagged as `v1.0.0`) to an ECR repository named `zacharygeorgebaker_backend`:
```
ecr_token=$(aws ecr get-login-password --region us-west-1);
docker login -u AWS -p $ecr_token 096206771424.dkr.ecr.us-west-1.amazonaws.com/zacharygeorgebaker_backend;
docker tag zacharygeorgebaker_backend:v1.0.0 096206771424.dkr.ecr.us-west-1.amazonaws.com/zacharygeorgebaker_backend:v1.0.0;
docker push 096206771424.dkr.ecr.us-west-1.amazonaws.com/zacharygeorgebaker_backend:v1.0.0;
```

Pushing can take a while if there are big dependencies (like tensorflow). Be patient.

<br/>

### Creating the lambda function

Create a new lambda function on AWS Lambda. Create this function from a __Container Image__ and supply the ECR Image URI of the container you pushed in the previous step. Set the architecture to __arm64__.

Navigate to the __Configuration__ tab. Set an appropriate __Timeout__ and __Memory__ if necessary.

Routes should be tested on this console - navigate to the __Test__ tab and run a test with an appropriate __Event JSON__ to confirm that routes work as expected. Below are example Event JSONs that are used to test various routes:

```
{
  "path": "/testGet",
  "httpMethod": "GET",
  "headers": {
    "Content-Type": "application/json",
    "Accept": "application/json"
  }
}
```

```
{
  "path": "/testPost",
  "httpMethod": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Accept": "application/json"
  },
  "body": "{\"key1\": \"value1\", \"key2\": \"value2\"}"
}
```

```
{
  "path": "/regfigs",
  "httpMethod": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Accept": "application/json"
  },
  "body": "{\"data_type\": \"exponential\", \"regress_type\": \"exponential\"}"
}
```

Note that `POST` Event JSONs must have a `"body"` that is a _stringified JSON_. Sorry about that.

You may find through testing that the Lambda has insufficient AWS IAM permissions (it's helpful to check __CloudWatch__ logs to confirm this). To update them, find the Lambda function's Role Name located under the __[Configuration tab -> Permissions -> Role name]__.

<br/>

### Creating the API

In AWS API Gateway Create a __REST API__ (click __Create API__ then the __Build__ button under __REST API__). Name it and make it regional (and make sure you're under the AWS region you want - the same as the Lambda function you made).

Now each route programmed in `app.py` must be created as a _resource_. To set up a route in this way, click __Create resource__ (make sure you create each resource under the right path - usually root `/`). Leave __Proxy resource__ off, set the __Resource Name__ the same as the route name (e.g. `testGet`, `testPost`, `regfigs`, etc.), and toggle __CORS__ on. You will see an `OPTIONS` method is created for this resource (leave this, it stops CORS from mucking up local frontend testing). Now for this resource click __Create method__. Select the metod type specified in `app.py` (e.g. `GET`, `POST`, etc.), select __Lambda function__ for Integration type, turn __Lambda proxy integration__ on, specify your Lambda function's ARN, and click __Create method__.

Once all resources and methods are created click __Deploy API__. Assign the API a stage (for example `dev`).

Be sure to test your methods. Click on a method under __Resources__ and navigate to the __Test__ tab. When testing `POST` methods be sure to include `Content-Type:application/json` (no quotes) in the __Headers__ and add a __Request Body__ (this JSON does _not_ have to be stringified).

Almost done. Navigate to the API's __Stages__ and copy the __Invoke URL__. Use this Invoke URL to test on postman or a browser to make sure that the URL works. If so, then the backend is working and can be used on the frontend!

<br/>

### Additional Notes:

- For the `regfigs` method the Lambda needs GetObject (for signed url generation) and PutObject S3 permisions
- Test your flask app locally by running `app.py` in your terminal/IDE.
- When using signed URLs to fetch objects from S3, you need to consider CORS for local development. In the S3 bucket on AWS under the Permissions tab use this for the CORS configuration:

```
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "PUT",
            "POST"
        ],
        "AllowedOrigins": [
            "*"
        ],
        "ExposeHeaders": []
    }
]
```

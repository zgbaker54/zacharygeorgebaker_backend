# zacharygeorgebaker_backend
Dockerized backend for zacharygeorgebaker.com using AWS ECR, Lambda, and API Gateway.

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
```

<br/>

## Creating this backend
These steps document my eventual solution in getting Docker, ECR, Lambda, and API Gateway working together.

<br/>

### Write a python function

Write a function in `app.py` with 2 arguments: `event` and `context`. `event` will be a python dict of the json payload sent in the body of the API call (GET/POST).

<br/>

### Building Docker container pointed at a function in `app.py`

See Dockerfile for complete code. `FROM public.ecr.aws/lambda/python:3.11` uses a python build made for lambda. `CMD [ "app.regfigs" ]` points the Container to run the `regfigs` function in `app.py`

Run the following line to build the Docker container named `zacharygeorgebaker_backend` and tagged as `v1.0.0`:
```
docker build -t zacharygeorgebaker_backend:v1.0.0 .;
```

Make sure to iterate the tag `v1.0.0` to be unique (check Docker (desktop) to see and delete already-existing builds).

<br/>

### Pushing the container to ECR

On AWS ECR make an ECR repository. The following code pushes the Docker container named `zacharygeorgebaker_backend` and tagged as `v1.0.0` to an ECR repository named `zacharygeorgebaker_backend`:
```
ecr_token=$(aws ecr get-login-password --region us-west-1);
docker login -u AWS -p $ecr_token 096206771424.dkr.ecr.us-west-1.amazonaws.com/zacharygeorgebaker_backend;
docker tag zacharygeorgebaker_backend:v1.0.0 096206771424.dkr.ecr.us-west-1.amazonaws.com/zacharygeorgebaker_backend:v1.0.0;
docker push 096206771424.dkr.ecr.us-west-1.amazonaws.com/zacharygeorgebaker_backend:v1.0.0;
```
Make sure to iterate the tag `v1.0.0` to be unique (check ECR on AWS to see and delete already-pushed builds).

<br/>

### Creating the lambda function

Create a new lambda function on AWS Lambda. Create this function from a `Container Image` and supply the ECR Image URI of the container you pushed in the previous step. Set the architecture to arm64. Once the function is created navigate to the `Test` tab and run a test with an appropriate Event JSON to confirm that the functionn works as expected. You may need to update the lambda's AWS IAM permissions (find the Role name located under the [Configuration tab -> Permissions -> Role name]). Also under the [Configuration tab -> General configuration] you can set the timeout and momeory.

<br/>

### Creating the API

In AWS API Gateway Create a REST API (click Create API then the Build button under REST API). Name it and make it regional (and make sure you're under the AWS region you want). Then click the Create Method button. Set Method type to ANY, set Integration Type to Lambda function, make sure Lambda proxy integration is off, and enter the ARN of the Lambda made in the previous step. After the method is created navigate to the Method's Test tab and run a test to make sure the method works as expected. Then click Deploy API and assign it a stage (for example `dev`). Then navigate to the API's Stages and copy the Invoke URL. Test on postman or a browser to make sure that this URL works. If so, then the backend is working and can be used!

<br/>

### Additional Notes:

- For the `regfigs` method the Lambda needs GetObject (for signed url generation) and PutObject S3 permisions
- After building a local Docker container you can run it with `docker run -p 9000:8080 zacharygeorgebaker_backend:v1.0.0` and then hit the url `http://localhost:9000/2015-03-31/functions/function/invocations` in postman or curl for local testing (though I've found difficulty getting AWS permissions here).
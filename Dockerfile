# lambda-specific python (lambda architecture must be arm64)
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY app.py ${LAMBDA_TASK_ROOT}

ENV CONTENT_TYPE=application/json

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.regfigs" ]
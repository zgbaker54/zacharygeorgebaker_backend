# lambda-specific python (lambda architecture must be arm64)
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY app.py ${LAMBDA_TASK_ROOT}

# Copy digits.py and digit keras model
COPY digits.py ${LAMBDA_TASK_ROOT}
COPY digit_nn_model.keras ${LAMBDA_TASK_ROOT}

# set content type in an env var
ENV CONTENT_TYPE=application/json

# Set the CMD to the handler (this is what the docker container runs)
CMD [ "app.handler" ]
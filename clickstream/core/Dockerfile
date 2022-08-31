FROM public.ecr.aws/lambda/python:3.9

# Install the function's dependencies using file requirements.txt
# from your project folder.
COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY env.py ${LAMBDA_TASK_ROOT}
COPY kinesis_producer.py ${LAMBDA_TASK_ROOT}
COPY lambda_app.py ${LAMBDA_TASK_ROOT}
COPY models.py ${LAMBDA_TASK_ROOT}
COPY routers ${LAMBDA_TASK_ROOT}/routers
COPY server.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_app.handler" ]

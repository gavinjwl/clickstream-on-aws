import os

allow_origins = os.environ.get('ALLOW_ORIGINS', None)
if allow_origins:
    allow_origins = allow_origins.split(',')
else:
    allow_origins = ['https://localhost:9000']

kinesis_stream_name = os.environ.get('KINESIS_STREAM_NAME', None)
write_key = os.environ.get('WRITE_KEY', None)

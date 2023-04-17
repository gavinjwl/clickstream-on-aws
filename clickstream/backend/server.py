from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from env import allow_origins
from routers import analytics_next, analytics_python

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
def index():
    return 'ok'


app.include_router(analytics_next.router)
app.include_router(analytics_python.router)

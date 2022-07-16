from mangum import Mangum

from server import app

handler = Mangum(app, lifespan="auto")

from fastapi import FastAPI
from .database import Base, engine
from . import models
from .routers import auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgriToken API")

app.include_router(auth_router.router)
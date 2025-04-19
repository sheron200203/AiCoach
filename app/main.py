from fastapi import FastAPI
from app.db.connection import Base, engine
from app.db import models
from app.api import auth

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

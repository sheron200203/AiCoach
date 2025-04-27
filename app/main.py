from fastapi import FastAPI
from app.api import auth, chatbot
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.db import models

app = FastAPI()
@app.on_event("startup")
def on_startup():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

# origins = [
#     "http://localhost:5173"
# ]
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.include_router(auth.router)
app.include_router(chatbot.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
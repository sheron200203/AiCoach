from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"charset": "utf8mb4"})

"""session maker func(custom session) returns a class, we save it in the variable sessionLocal. to talk 
to the db we need to create objects from this (auth.dependencies = db)."""
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
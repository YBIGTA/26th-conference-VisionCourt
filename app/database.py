from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()
user = os.getenv("user")
password = quote_plus(os.getenv("password"))
host = os.getenv("host")
port = os.getenv("port")
name = os.getenv("dbname")


DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{name}"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 요청마다 DB 세션 열고 닫는 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

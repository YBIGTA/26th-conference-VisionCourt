from fastapi import FastAPI
from app import models, database, crud, schemas
from app.database import engine
from sqlalchemy.orm import Session
from fastapi import Depends

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/actions/")
def create_action(action: schemas.ActionIn, db: Session = Depends(database.get_db)):
    return crud.insert_action_from_json(db, action)

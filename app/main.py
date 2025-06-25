from fastapi import FastAPI, HTTPException
from app import models, database, crud, schemas
from app.database import engine
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import List

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/actions/")
def create_action(action: schemas.ActionIn, db: Session = Depends(database.get_db)):
    return crud.insert_action_from_json(db, action)

@app.get("/games", response_model=List[schemas.GameSchema])
def read_games(db: Session = Depends(database.get_db)):
    """모든 게임의 기본 정보와 점수를 조회합니다."""
    return crud.get_all_games(db)

@app.get("/games/{game_id}", response_model=schemas.GameDetailSchema)
def read_game_detail(game_id: int, db: Session = Depends(database.get_db)):
    """특정 게임의 상세 정보를 조회합니다."""
    game = crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
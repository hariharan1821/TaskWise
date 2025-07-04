from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import redis
import json
from database import Base, SessionLocal, engine

import models, schemas, crud

models.init_db()

app = FastAPI(title="TaskWise")
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Dependency to get DB session
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.get("/tasks/", response_model=List[schemas.Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cache_key = f"tasks_{skip}_{limit}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    tasks = crud.get_tasks(db, skip=skip, limit=limit)
    tasks_data = [schemas.Task.from_orm(task).dict() for task in tasks]
    redis_client.set(cache_key, json.dumps(tasks_data), ex=30)
    return tasks_data

@app.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    user = crud.get_user(db, 1)
    if not user:
        user = crud.create_user(db, schemas.UserCreate(username="default"))
    new_task = crud.create_task(db, task, user_id=user.id)
    
    for k in redis_client.keys("tasks_*"):
        redis_client.delete(k)
    return schemas.Task.from_orm(new_task)

@app.get("/tasks/{task_id}", response_model=schemas.Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.delete("/tasks/{task_id}", response_model=schemas.Task)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.delete_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    for k in redis_client.keys("tasks_*"):
        redis_client.delete(k)
    return db_task
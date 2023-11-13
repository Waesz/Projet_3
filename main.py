from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import List
from sqlalchemy.dialects.mysql import mysqlconnector

DATABASE_URL = "mysql+mysqlconnector://root:test@localhost/prj3"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

app = FastAPI()


# Créez une classe modèle SQLAlchemy pour les tâches
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(
        String(255), index=True
    )  # Spécifiez une longueur maximale de 255 caractères
    description = Column(String(255))


# Créez une classe modèle Pydantic pour les tâches
class TaskCreate(BaseModel):
    title: str
    description: str


# Créez la table et toutes les autres tables
Base.metadata.create_all(bind=engine)


# ROUTES INSCRIPTION ET CONNEXION
@app.get("/register")
async def register():
    return {"message": "Inscription d'un nouvel utilisateur"}


@app.post("/login")
async def login():
    return {"message": "Connexion d'un utilisateur"}


# ROUTES POUR LES TASKS
@app.get("/tasks", response_model=List[TaskCreate])
async def get_tasks():
    db = SessionLocal()
    tasks = db.query(Task).all()
    db.close()
    return tasks


@app.post("/tasks", response_model=TaskCreate)
async def post_tasks(task: TaskCreate):
    db = SessionLocal()
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    db.close()
    return db_task


@app.get("/tasks/{task_id}", response_model=TaskCreate)
async def get_tasksbyid(task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    db.close()
    if task is None:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return task


@app.put("/tasks/{task_id}", response_model=TaskCreate)
async def put_tasksbyid(task_id: int, updated_task: TaskCreate):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        db.close()
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    for key, value in updated_task.dict().items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    db.close()
    return task


@app.delete("/tasks/{task_id}", response_model=TaskCreate)
async def delete_tasksbyid(task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        db.close()
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    db.delete(task)
    db.commit()
    db.close()
    return task

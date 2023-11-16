from datetime import date
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import List
from sqlalchemy.dialects.mysql import mysqlconnector
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

DATABASE_URL = "postgresql://postgres:Nenany20@localhost/projet3"

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
    user_id = Column(Integer, ForeignKey('users.id'))  # ForeignKey to users table

    # Establish the relationship between Task and User
    user = relationship("User", back_populates="tasks")

# Créez une classe modèle SQLAlchemy pour les utilisateurs
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
    tasks = relationship("Task", back_populates="user")

# Creéz une classe modèle Pydantic pour les tâches
class UserCreate(BaseModel):
    id: int
    name: str
    email: str
    password: str

# Créez une classe modèle Pydantic pour les tâches
class TaskCreate(BaseModel):
    id: int
    title: str
    description: str
    status: str
    dateDeb: date
    dateFin: date
    user_id:int
# Créez la table et toutes les autres tables
Base.metadata.create_all(bind=engine)

# ROUTES INSCRIPTION ET CONNEXION
@app.get("/register")
async def register():
    return {"message": "Inscription d'un nouvel utilisateur"}


@app.post("/login")
async def login():
    return {"message": "Connexion d'un utilisateur"}

# ROUTES POUR LES Users
@app.get("/users", response_model=List[UserCreate])
async def getUsers():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return [{"name": user.name, "email": user.email} for user in users]

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

# un jeu de données pour les modeles

# Fonction pour insérer des utilisateurs dans la base de données
def create_users():
    db = SessionLocal()
    try:
        users_data = [
            {"name": "Alice", "email": "alice@example.com", "password": "pass123"},
            {"name": "Bob", "email": "bob@example.com", "password": "pass456"},
            {"name": "Charlie", "email": "charlie@example.com", "password": "pass789"},
        ]
        for user_data in users_data:
            user = User(**user_data)
            db.add(user)
        db.commit()
    finally:
        db.close()

# Fonction pour insérer des tâches dans la base de données
def create_tasks():
    db = SessionLocal()
    try:
        tasks_data = [
            {"title": "Task 1", "description": "Description for Task 1", "user_id": 1},
            {"title": "Task 2", "description": "Description for Task 2", "user_id": 2},
            {"title": "Task 3", "description": "Description for Task 3", "user_id": 3},
        ]
        for task_data in tasks_data:
            task = Task(**task_data)
            db.add(task)
        db.commit()
    finally:
        db.close()

# Appel des fonctions pour insérer les données
create_users()
create_tasks()


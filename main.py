import jwt
from datetime import date, datetime, timedelta
from typing import List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import Mapped

SECRET_KEY = "votre_clé_secrète"  # Remplacez par une clé secrète réelle
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Durée de validité du jeton en minutes
DATABASE_URL = "postgresql://postgres:test@90.63.38.240/prj3v2"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(
        String(255), index=True
    )  # Spécifiez une longueur maximale de 255 caractères
    description = Column(String(255))


# Créez une classe modèle Pydantic pour les tâches
class TaskCreate(BaseModel):
    id: int
    title: str
    description: str
    status: str
    dateDeb: date
    dateFin: date


# Modèle Pydantic pour la création d'un nouvel utilisateur
class UserCreate(BaseModel):
    login: str
    Email: str
    Password: str
    Firstname: str
    Lastname: str


class UserResponse(BaseModel):
    ID: int
    login: str
    Email: str
    Firstname: str
    Lastname: str
    CreationDate: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


# Créez une classe modèle SQLAlchemy pour les utilisateurs
class User(Base):
    __tablename__ = "users"

    ID = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    Email = Column(String, unique=True, index=True)
    Password = Column(String)
    Firstname = Column(String)
    Lastname = Column(String)
    CreationDate = Column(Date)


# Créez la table et toutes les autres tables
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ROUTES INSCRIPTION ET CONNEXION
@app.post("/register")
async def register(user: UserCreate):
    db = SessionLocal()
    # Hasher le mot de passe avant de le stocker
    hashed_password = hash_password(user.Password)

    # Obtenez la date actuelle
    current_date = date.today()

    # Créez un nouvel utilisateur avec le mot de passe hashé et la date actuelle
    db_user = User(
        login=user.login,
        Email=user.Email,
        Password=hashed_password,
        Firstname=user.Firstname,
        Lastname=user.Lastname,
        CreationDate=current_date,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "Inscription d'un nouvel utilisateur réussie"}


def hash_password(password: str):
    return pwd_context.hash(password)


@app.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.login == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.Password):
        raise HTTPException(
            status_code=401, detail="Nom d'utilisateur ou mot de passe incorrect"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.login}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    # Récupérez l'utilisateur depuis la base de données en fonction de son ID
    user = db.query(User).filter(User.ID == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Créez une instance de UserResponse à partir des données de l'utilisateur
    user_response = UserResponse(
        ID=user.ID,
        login=user.login,
        Email=user.Email,
        Firstname=user.Firstname,
        Lastname=user.Lastname,
        CreationDate=user.CreationDate.strftime(
            "%Y-%m-%d"
        ),  # Formatez la date selon vos besoins
    )

    return user_response


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


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

import jwt
from datetime import date, datetime, timedelta
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship


SECRET_KEY = "votre_clé_secrète"  # Remplacez par une clé secrète réelle
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Durée de validité du jeton en minutes
DATABASE_URL = "mysql+mysqlconnector://root:@127.0.0.1/prj3v3"

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
    status = Column(String(255))
    dateDeb = Column(Date)
    dateFin = Column(Date)
    user_id = Column(Integer, ForeignKey("users.ID"))
    user = relationship("User", back_populates="Tasks")


# Créez une classe modèle Pydantic pour les tâches
class TaskCreate(BaseModel):
    title: str
    description: str
    status: str
    dateDeb: date
    dateFin: date
    user_id: int


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
    login = Column(String(255), unique=True, index=True)
    Email = Column(String(255), unique=True, index=True)
    Password = Column(String(255))
    Firstname = Column(String(255))
    Lastname = Column(String(255))
    CreationDate = Column(Date)
    Tasks = relationship("Task", back_populates="user")


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
async def login(login: str, password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.login == login).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Login incorrect")
    if not verify_password(password, db_user.Password):
        raise HTTPException(status_code=400, detail="Mot de passe incorrect")

    # Générer un token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.login}, expires_delta=access_token_expires
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


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
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
    # db_task.user_id = db.get(User, 1).ID
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

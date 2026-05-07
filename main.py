from fastapi import FastAPI, HTTPException, Depends, Request, status
from starlette.middleware.sessions import SessionMiddleware   
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from pydantic import ConfigDict
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime
import db_manager as database   # импорт модуля из этапа 3, но редактированный для сервера

app = FastAPI(title="Календарь событий API", version="1.0")
app.add_middleware(SessionMiddleware, secret_key="supersecretkey_for_dev")

# Хэширование паролей
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = database.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user   # возвращает sqlite3.Row с полями id, username, email, password, role

def get_current_admin(current_user=Depends(get_current_user)):
    # role может отсутствовать в старой БД, по умолчанию 'user'
    role = current_user.get("role", "user")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin rights required")
    return current_user

# схемы pydantic

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^\S+@\S+\.\S+$", example="user@example.com")
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    event_date: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    notification_enabled: bool = False
    notification_time: Optional[datetime] = None

    @field_validator('event_date')
    @classmethod
    def not_in_past(cls, v: datetime) -> datetime:
        if v < datetime.now():
            raise ValueError('Event date cannot be in the past')
        return v

    @field_validator('notification_time')
    @classmethod
    def notification_before_event(cls, v: Optional[datetime], info: ValidationInfo) -> Optional[datetime]:
        if v is not None:
            event_date = info.data.get('event_date')
            if event_date and v > event_date:
                raise ValueError('Notification time must be before event date')
        return v

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    event_date: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    notification_enabled: Optional[bool] = None
    notification_time: Optional[datetime] = None

    @field_validator('event_date')
    @classmethod
    def not_in_past(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v < datetime.now():
            raise ValueError('Event date cannot be in the past')
        return v

    @field_validator('notification_time')
    @classmethod
    def notification_before_event(cls, v: Optional[datetime], info: ValidationInfo) -> Optional[datetime]:
        if v is not None:
            event_date = info.data.get('event_date')
            if event_date and v > event_date:
                raise ValueError('Notification time must be before event date')
        return v

class EventOut(BaseModel):
    id: int
    user_id: int
    title: str
    event_date: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    notification_enabled: bool
    notification_time: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class HolidayCreate(BaseModel):
    name: str
    date: str   # "год-месяц-день"
    description: str

class HolidayOut(BaseModel):
    id: int
    name: str
    date: str
    description: str

def row_to_dict(row):
    return dict(row) if row else None

# Эндпоинты для начала
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, request: Request):
    existing = database.get_user_by_username(user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed = hash_password(user.password)
    user_id = database.create_user(user.username, user.email, hashed)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Email already registered")
    # автоматический вход после регистрации
    request.session["user_id"] = user_id
    request.session["username"] = user.username
    return {"message": "User created and logged in", "user_id": user_id}

@app.post("/login")
async def login(user: UserLogin, request: Request):
    db_user = database.get_user_by_username(user.username)
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    request.session["user_id"] = db_user["id"]
    request.session["username"] = db_user["username"]
    return {"message": "Logged in successfully", "user_id": db_user["id"]}

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}

@app.get("/me")
async def me(current_user=Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "role": current_user.get("role", "user")
    }

# Эндпоинты событий (псоле авторизации)
@app.get("/events", response_model=list[EventOut])
async def get_my_events(current_user=Depends(get_current_user)):
    rows = database.get_events_by_user(current_user["id"])
    return [row_to_dict(row) for row in rows]

@app.get("/events/{event_id}", response_model=EventOut)
async def get_event(event_id: int, current_user=Depends(get_current_user)):
    row = database.get_event_by_id(event_id)
    if not row or row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Event not found")
    return row_to_dict(row)

@app.post("/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, current_user=Depends(get_current_user)):
    new_id = database.create_event(
        user_id=current_user["id"],
        title=event.title,
        event_date=event.event_date,
        description=event.description,
        location=event.location,
        image_url=event.image_url,
        notification_enabled=event.notification_enabled,
        notification_time=event.notification_time
    )
    created = database.get_event_by_id(new_id)
    return row_to_dict(created)

@app.put("/events/{event_id}", response_model=EventOut)
async def update_event(event_id: int, event_update: EventUpdate, current_user=Depends(get_current_user)):
    existing = database.get_event_by_id(event_id)
    if not existing or existing["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Event not found")
    update_data = event_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    # проверка дат 
    new_event_date = update_data.get("event_date", existing["event_date"])
    if new_event_date < datetime.now():
        raise HTTPException(status_code=400, detail="Event date cannot be in the past")
    new_notify = update_data.get("notification_time")
    if new_notify and new_notify > new_event_date:
        raise HTTPException(status_code=400, detail="Notification time must be before event date")
    success = database.update_event(event_id, **update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Update failed")
    updated = database.get_event_by_id(event_id)
    return row_to_dict(updated)

@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, current_user=Depends(get_current_user)):
    existing = database.get_event_by_id(event_id)
    if not existing or existing["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Event not found")
    database.delete_event(event_id)
    return

# для праздников доступно всем

@app.get("/holidays", response_model=list[HolidayOut])
async def get_holidays():
    rows = database.get_all_holidays()
    return [row_to_dict(row) for row in rows]

# Эндпоинты для admin

@app.post("/admin/holidays", response_model=HolidayOut, status_code=201)
async def create_holiday(holiday: HolidayCreate, admin=Depends(get_current_admin)):
    new_id = database.add_holiday(holiday.name, holiday.date, holiday.description)
    # вернём созданный праздник (получим его заново)
    all_holidays = database.get_all_holidays()
    for h in all_holidays:
        if h["id"] == new_id:
            return row_to_dict(h)
    raise HTTPException(status_code=500, detail="Failed to retrieve created holiday")

@app.delete("/admin/holidays/{holiday_id}", status_code=204)
async def delete_holiday(holiday_id: int, admin=Depends(get_current_admin)):
    success = database.delete_holiday(holiday_id)
    if not success:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return

# корень всеначало
@app.get("/")
async def root():
    return {"message": "Calendar API is running", "docs": "/docs"}
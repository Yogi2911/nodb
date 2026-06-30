from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from auth_utils import hash_password, verify_password, create_access_token
import store

router = APIRouter()

class RegisterIn(BaseModel):
    name:     str
    email:    EmailStr
    password: str

class LoginIn(BaseModel):
    email:    EmailStr
    password: str

@router.post("/register", status_code=201)
def register(payload: RegisterIn):
    # Check email already exists
    for u in store.users.values():
        if u["email"] == payload.email:
            raise HTTPException(400, "Email already registered")

    uid = store.next_id("users")
    store.users[uid] = {
        "id":       uid,
        "name":     payload.name,
        "email":    payload.email,
        "password": hash_password(payload.password),
        "is_admin": False
    }
    return {"id": uid, "name": payload.name, "email": payload.email, "is_admin": False}

@router.post("/login")
def login(payload: LoginIn):
    user = next((u for u in store.users.values() if u["email"] == payload.email), None)
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "bearer"}

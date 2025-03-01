from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any
from ..services.auth import auth_service

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/signup")
async def signup(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, Any]:
    try:
        response = await auth_service.sign_up(form_data.username, form_data.password)
        return {
            "message": "User created successfully",
            "user": response
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, Any]:
    try:
        response = await auth_service.sign_in(form_data.username, form_data.password)
        return {
            "access_token": response["session"]["access_token"],
            "refresh_token": response["session"]["refresh_token"],
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    try:
        await auth_service.sign_out(token)
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    user = await auth_service.get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@router.post("/refresh")
async def refresh_token(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    try:
        response = await auth_service.refresh_token(token)
        return {
            "access_token": response["session"]["access_token"],
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token") 
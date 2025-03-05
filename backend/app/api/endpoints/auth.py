from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
from ..services.auth import auth_service

router = APIRouter()

class OAuth2PasswordBearerWithQuery(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        # First try to get the token from query parameters
        token = request.query_params.get("access_token")
        if token:
            # Verify the token is valid
            user = await auth_service.get_user(token)
            if user:
                return token
        # If not in query params or invalid, try the normal authorization header
        return await super().__call__(request)

oauth2_scheme = OAuth2PasswordBearerWithQuery(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user_data = await auth_service.get_user(token)
        if not user_data or not user_data.get("user"):
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_data
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

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
async def logout(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, str]:
    try:
        await auth_service.sign_out(user["access_token"])
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return user

@router.post("/refresh")
async def refresh_token(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        response = await auth_service.refresh_token(user["refresh_token"])
        return {
            "access_token": response["session"]["access_token"],
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token") 
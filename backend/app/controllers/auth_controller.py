from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.services.auth_service import AuthService, InvalidCredentials


router = APIRouter(prefix='/api/auth', tags=['Authentication'])


def get_auth_service(request: Request, db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db), request.app.state.tokens, request.app.state.dummy_hash)


@router.post('/login', response_model=LoginResponse, responses={400:{'description':'Invalid request'},401:{'description':'Invalid credentials'}})
def login(payload: LoginRequest, response: Response, service: AuthService = Depends(get_auth_service)) -> LoginResponse:
    try:
        result = service.login(payload.email, payload.password)
    except InvalidCredentials as exc:
        raise HTTPException(401, 'Invalid credentials', headers={'WWW-Authenticate':'Bearer','Cache-Control':'no-store'}) from exc
    response.headers['Cache-Control'] = 'no-store'
    return LoginResponse(token=result.token, user=UserResponse(userId=result.user_id, name=result.name, role=result.role))

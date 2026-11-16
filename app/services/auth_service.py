import jwt

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def signup(self, data: UserCreate) -> User:
        if self.user_repo.get_by_email(data.email):
            raise ConflictError("이미 사용 중인 이메일입니다.")
        if self.user_repo.get_by_username(data.username):
            raise ConflictError("이미 사용 중인 사용자 이름입니다.")
        return self.user_repo.create(data.email, data.username, hash_password(data.password))

    def login(self, data: UserLogin) -> str:
        user = self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("이메일 또는 비밀번호가 올바르지 않습니다.")
        return create_access_token(user.id)

    def get_user_from_token(self, token: str) -> User:
        try:
            user_id = decode_access_token(token)
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("토큰이 만료되었습니다.")
        except jwt.PyJWTError:
            raise UnauthorizedError("유효하지 않은 토큰입니다.")
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedError("존재하지 않는 사용자입니다.")
        return user

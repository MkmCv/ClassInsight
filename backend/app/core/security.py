"""
安全相关：密码哈希、JWT Token 生成与验证
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings

# 尝试使用 bcrypt 直接实现，如果失败则回退到 passlib
try:
    import bcrypt
    USE_DIRECT_BCRYPT = True
except ImportError:
    USE_DIRECT_BCRYPT = False

# 密码加密上下文
# 使用 bcrypt 方案，并指定兼容的配置
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # 指定轮数
    bcrypt__ident="2b"  # 使用 2b 标识符（更兼容）
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        # 如果密码超过72字节，先截断（bcrypt限制）
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # 如果 passlib 失败，尝试直接使用 bcrypt
        if USE_DIRECT_BCRYPT:
            try:
                password_bytes = plain_password.encode('utf-8')
                if len(password_bytes) > 72:
                    password_bytes = password_bytes[:72]
                hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
                return bcrypt.checkpw(password_bytes, hash_bytes)
            except Exception:
                # 如果直接使用 bcrypt 也失败，抛出原始错误
                pass
        # 重新抛出原始错误
        raise e


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    try:
        # 如果密码超过72字节，先截断（bcrypt限制）
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(password)
    except Exception as e:
        # 如果 passlib 失败，尝试直接使用 bcrypt
        if USE_DIRECT_BCRYPT:
            try:
                password_bytes = password.encode('utf-8')
                if len(password_bytes) > 72:
                    password_bytes = password_bytes[:72]
                salt = bcrypt.gensalt(rounds=12)
                hashed = bcrypt.hashpw(password_bytes, salt)
                return hashed.decode('utf-8')
            except Exception:
                # 如果直接使用 bcrypt 也失败，抛出原始错误
                pass
        # 重新抛出原始错误
        raise e


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None






















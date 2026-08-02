import os

SECRET_KEY = os.getenv("SECRET_KEY", "levelup-super-secret-jwt-key-2026-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 *7
DATABASE_PATH = os.getenv("DATABASE_PATH", "levelup.db")
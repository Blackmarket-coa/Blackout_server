import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://blackout:blackout@localhost:5432/blackout")
SYNAPSE_URL = os.environ.get("SYNAPSE_URL", "http://localhost:8008")
SYNAPSE_ADMIN_TOKEN = os.environ.get("SYNAPSE_ADMIN_TOKEN", "")
REGISTRATION_SHARED_SECRET = os.environ.get("REGISTRATION_SHARED_SECRET", "")

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "72"))

CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if o.strip()
]

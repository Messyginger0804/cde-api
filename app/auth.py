from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import API_TOKEN

scheme = HTTPBearer(auto_error=False)

def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(scheme)):
    if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

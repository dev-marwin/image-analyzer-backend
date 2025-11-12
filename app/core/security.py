import logging

from fastapi import HTTPException, status
from supabase import Client, create_client

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SupabaseAuthVerifier:

    def __init__(self) -> None:
        self.supabase_url = settings.supabase_url
        self.supabase_anon_key = settings.supabase_anon_key
        
        if not self.supabase_anon_key:
            logger.warning(
                "SUPABASE_ANON_KEY not set. Token verification may fail. "
                "Get it from Supabase Settings → API → anon public key"
            )
        
        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_anon_key or "")
        except Exception as e:
            logger.error("Failed to create Supabase client for auth: %s", e)
            self.client = None

    def verify_token(self, token: str) -> dict:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
            )

        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service not configured",
            )

        try:
            import httpx
            
            verify_url = f"{self.supabase_url}/auth/v1/user"
            headers = {
                "Authorization": f"Bearer {token}",
                "apikey": self.supabase_anon_key,
            }
            
            verify_response = httpx.get(verify_url, headers=headers, timeout=5.0)
            
            if verify_response.status_code == 200:
                user_data = verify_response.json()
                return {
                    "sub": user_data.get("id"),
                    "user_id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "user_metadata": user_data.get("user_metadata", {}),
                }
            elif verify_response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication token",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Authentication failed: {verify_response.status_code}",
                )
        except httpx.RequestError as e:
            logger.error("Supabase Auth API request failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Supabase Auth verification failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

    def get_user_id(self, token: str) -> str:
        user_info = self.verify_token(token)
        user_id = user_info.get("sub") or user_info.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain user_id",
            )
        return str(user_id)


auth_verifier = SupabaseAuthVerifier()

from typing import Any, Dict, Optional

from supabase import Client, create_client

from ..core.config import get_settings

settings = get_settings()


class ImageRepository:

    def __init__(self) -> None:
        self.client: Client = create_client(settings.supabase_url, settings.supabase_service_key)

    def create_image(self, *, user_id: str, filename: str, original_path: str, thumbnail_path: Optional[str] = None) -> Dict[str, Any]:
        data = {
            "user_id": user_id,
            "filename": filename,
            "original_path": original_path,
            "thumbnail_path": thumbnail_path,
        }
        response = self.client.table("images").insert(data).execute()
        if not response.data or len(response.data) == 0:
            raise RuntimeError("Failed to create image record")
        return response.data[0]

    def create_initial_metadata(self, *, image_id: int, user_id: str, status: str = "pending") -> Dict[str, Any]:
        data = {
            "image_id": image_id,
            "user_id": user_id,
            "ai_processing_status": status,
        }
        response = self.client.table("image_metadata").insert(data).execute()
        if not response.data or len(response.data) == 0:
            raise RuntimeError("Failed to create metadata record")
        return response.data[0]

    def get_metadata(self, image_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        response = (
            self.client.table("image_metadata")
            .select("*")
            .eq("image_id", image_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not response.data:
            return None
        return response.data[0]

    def upsert_metadata(
        self,
        image_id: int,
        user_id: str,
        *,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        colors: Optional[list[str]] = None,
        status: str,
    ) -> None:
        existing = self.get_metadata(image_id, user_id)
        payload: Dict[str, Any] = {
            "image_id": image_id,
            "user_id": user_id,
            "ai_processing_status": status,
        }
        if description is not None:
            payload["description"] = description
        if tags is not None:
            payload["tags"] = tags
        if colors is not None:
            payload["colors"] = colors

        if existing:
            self.client.table("image_metadata").update(payload).eq("id", existing["id"]).execute()
        else:
            self.client.table("image_metadata").insert(payload).execute()

    def update_thumbnail_path(self, image_id: int, thumbnail_path: str) -> None:
        self.client.table("images").update({"thumbnail_path": thumbnail_path}).eq("id", image_id).execute()

    def verify_image_ownership(self, image_id: int, user_id: str) -> bool:
        response = (
            self.client.table("images")
            .select("id, user_id")
            .eq("id", image_id)
            .eq("user_id", user_id)
            .execute()
        )
        return len(response.data) > 0


class StorageRepository:

    def __init__(self) -> None:
        self.client: Client = create_client(settings.supabase_url, settings.supabase_service_key)
        self.bucket = settings.supabase_bucket

    def download_original(self, path: str) -> bytes:
        response = self.client.storage.from_(self.bucket).download(path)
        if isinstance(response, bytes):
            return response
        raise RuntimeError(f"Unable to download file from storage path: {path}")

    def upload_thumbnail(self, path: str, data: bytes, content_type: str = "image/jpeg") -> str:
        self.client.storage.from_(self.bucket).upload(
            path, data, {"content-type": content_type}
        )
        return path

    def upload_original(self, path: str, data: bytes, content_type: str = "image/jpeg") -> str:
        self.client.storage.from_(self.bucket).upload(
            path, data, {"content-type": content_type}
        )
        return path


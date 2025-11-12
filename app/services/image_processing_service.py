import logging
import uuid

from ..core.config import get_settings
from ..repositories.image_repository import ImageRepository, StorageRepository
from ..services.ai_service import AIService
from ..utils.image_utils import create_thumbnail, extract_dominant_colors

logger = logging.getLogger(__name__)
settings = get_settings()


class ImageProcessingService:

    def __init__(self) -> None:
        self.image_repo = ImageRepository()
        self.storage_repo = StorageRepository()
        self.ai_service = AIService()

    def process_image(
        self,
        image_id: int,
        user_id: str,
        original_path: str,
    ) -> None:
        logger.info("Starting image processing: image_id=%s, user_id=%s", image_id, user_id)

        try:
            if not self.image_repo.verify_image_ownership(image_id, user_id):
                logger.error("Image %s does not belong to user %s", image_id, user_id)
                raise ValueError(f"Image {image_id} does not belong to user {user_id}")

            existing = self.image_repo.get_metadata(image_id, user_id)
            if existing and existing.get("ai_processing_status") == "completed":
                logger.info("Image %s already processed. Skipping.", image_id)
                return

            self.image_repo.upsert_metadata(image_id, user_id, status="processing")
            logger.info("Downloading original image from: %s", original_path)

            original_bytes = self.storage_repo.download_original(original_path)
            logger.info("Image downloaded, size: %d bytes", len(original_bytes))

            logger.info("Generating thumbnail...")
            thumbnail_bytes = create_thumbnail(original_bytes, size=settings.thumbnail_size)
            thumbnail_path = f"{user_id}/thumbnails/{uuid.uuid4()}.jpg"
            self.storage_repo.upload_thumbnail(thumbnail_path, thumbnail_bytes)
            self.image_repo.update_thumbnail_path(image_id, thumbnail_path)
            logger.info("Thumbnail uploaded to: %s", thumbnail_path)

            logger.info("Extracting dominant colors...")
            colors = extract_dominant_colors(original_bytes, top_n=3)
            logger.info("Extracted colors: %s", colors)

            logger.info("Starting AI analysis...")
            analysis = self.ai_service.analyze_image(original_bytes)
            tags = analysis.get("tags", [])  # type: ignore[arg-type]
            description = analysis.get("description", "")
            logger.info("AI analysis complete. Tags: %d, Description length: %d", len(tags), len(description))

            self.image_repo.upsert_metadata(
                image_id,
                user_id,
                description=description if isinstance(description, str) else "",
                tags=tags if isinstance(tags, list) else [],
                colors=colors,
                status="completed",
            )
            logger.info("Successfully processed image_id=%s", image_id)
        except Exception as exc:
            logger.exception("Failed to process image_id=%s: %s", image_id, exc)
            try:
                self.image_repo.upsert_metadata(image_id, user_id, status="failed")
            except Exception as update_exc:
                logger.error("Failed to update status to 'failed': %s", update_exc)
            raise


image_processing_service = ImageProcessingService()

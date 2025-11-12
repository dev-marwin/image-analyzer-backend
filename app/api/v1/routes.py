import logging
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from ...middleware.auth import get_current_user
from ...schemas.image import HealthResponse, ProcessImageRequest, ProcessImageResponse
from ...services.image_processing_service import image_processing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["images"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/images/process",
    response_model=ProcessImageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process image with AI",
    description="Enqueue an image for background processing with AI analysis",
)
async def process_image(
    request: ProcessImageRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user),
) -> ProcessImageResponse:
    if not image_processing_service.image_repo.verify_image_ownership(
        request.image_id, current_user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to process this image",
        )

    logger.info(
        "Enqueuing image processing: image_id=%s, user_id=%s",
        request.image_id,
        current_user_id,
    )

    background_tasks.add_task(
        image_processing_service.process_image,
        request.image_id,
        current_user_id,
        request.original_path,
    )

    return ProcessImageResponse(status="queued", image_id=request.image_id)


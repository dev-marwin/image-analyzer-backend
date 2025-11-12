import logging
import uuid
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from ...middleware.auth import get_current_user
from ...schemas.image import (
    HealthResponse,
    ProcessImageRequest,
    ProcessImageResponse,
    RegisterImageRequest,
    RegisterImageResponse,
    UploadImageResponse,
)
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


@router.post(
    "/images/register",
    response_model=RegisterImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register uploaded image",
    description="Register an uploaded image record and create initial metadata using service role privileges.",
)
async def register_image(
    request: RegisterImageRequest,
    current_user_id: str = Depends(get_current_user),
) -> RegisterImageResponse:
    logger.info(
        "Registering image for user_id=%s filename=%s",
        current_user_id,
        request.filename,
    )

    try:
        image_record = image_processing_service.image_repo.create_image(
            user_id=current_user_id,
            filename=request.filename,
            original_path=request.original_path,
        )
        image_processing_service.image_repo.create_initial_metadata(
            image_id=image_record["id"],
            user_id=current_user_id,
            status="pending",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to register image: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register image",
        ) from exc

    return RegisterImageResponse(image_id=image_record["id"], status="registered")


@router.post(
    "/images/upload",
    response_model=UploadImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload image file",
    description="Upload an image file to storage and register it in the database. Handles both storage and database operations using service role privileges.",
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user_id: str = Depends(get_current_user),
) -> UploadImageResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    file_content = await file.read()
    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    object_path = f"{current_user_id}/original/{uuid.uuid4()}.{extension}"

    logger.info(
        "Uploading image: filename=%s, user_id=%s, path=%s",
        file.filename,
        current_user_id,
        object_path,
    )

    try:
        image_processing_service.storage_repo.upload_original(
            path=object_path,
            data=file_content,
            content_type=file.content_type,
        )

        image_record = image_processing_service.image_repo.create_image(
            user_id=current_user_id,
            filename=file.filename or "uploaded_image",
            original_path=object_path,
        )

        image_processing_service.image_repo.create_initial_metadata(
            image_id=image_record["id"],
            user_id=current_user_id,
            status="pending",
        )

        background_tasks.add_task(
            image_processing_service.process_image,
            image_record["id"],
            current_user_id,
            object_path,
        )

        logger.info("Image uploaded and registered: image_id=%s", image_record["id"])

        return UploadImageResponse(
            image_id=image_record["id"],
            original_path=object_path,
            status="uploaded",
        )

    except Exception as exc:
        logger.exception("Failed to upload image: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(exc)}",
        ) from exc


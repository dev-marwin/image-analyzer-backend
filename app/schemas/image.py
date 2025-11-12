from pydantic import BaseModel, Field


class ProcessImageRequest(BaseModel):
    """Request schema for image processing."""

    image_id: int = Field(..., gt=0, description="Image ID from database")
    original_path: str = Field(..., min_length=1, description="Path to original image in storage")
    filename: str = Field(..., min_length=1, description="Original filename")

    class Config:
        json_schema_extra = {
            "example": {
                "image_id": 123,
                "original_path": "user-id/original/image.jpg",
                "filename": "vacation.jpg",
            }
        }


class ProcessImageResponse(BaseModel):
    """Response schema for image processing request."""

    status: str = Field(..., description="Processing status")
    image_id: int = Field(..., description="Image ID")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "queued",
                "image_id": 123,
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")

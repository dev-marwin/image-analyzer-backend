from pydantic import BaseModel, Field


class ProcessImageRequest(BaseModel):

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

    status: str = Field(..., description="Processing status")
    image_id: int = Field(..., description="Image ID")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "queued",
                "image_id": 123,
            }
        }


class UploadImageResponse(BaseModel):

    image_id: int = Field(..., description="Image ID in database")
    original_path: str = Field(..., description="Path to uploaded image in storage")
    status: str = Field(..., description="Upload status")


class HealthResponse(BaseModel):

    status: str = Field(..., description="Service status")


class RegisterImageRequest(BaseModel):

    filename: str = Field(..., min_length=1, description="Original filename")
    original_path: str = Field(..., min_length=1, description="Path to original image in storage")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "sunset.jpg",
                "original_path": "user-id/original/f1b2c3d4e5.jpg",
            }
        }


class RegisterImageResponse(BaseModel):

    image_id: int = Field(..., description="Created image ID")
    status: str = Field(..., description="Registration status")

    class Config:
        json_schema_extra = {
            "example": {
                "image_id": 456,
                "status": "registered",
            }
        }

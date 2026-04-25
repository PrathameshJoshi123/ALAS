from pydantic import BaseModel, Field


class PDFUploadSchema(BaseModel):
    """Schema for PDF file upload with company name"""
    company_name: str = Field(..., min_length=1, description="Name of the company")

    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Acme Corp"
            }
        }

"""Core FastAPI router for C.R.E.A.T.E. framework API endpoints.

This module provides the essential API endpoints for Phase 1 Issue 4,
implementing the basic C.R.E.A.T.E. framework functionality.
"""

import time

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.api.models.create_models_core import (
    CreateRequestModel,
    CreateResponseModel,
    DomainResponseModel,
    ErrorResponseModel,
    FrameworkInfoResponseModel,
    HealthResponseModel,
)
from src.core.create_processor_core import CreateProcessor, ValidationError

# Initialize router
router = APIRouter(
    prefix="/api/v1/create",
    tags=["create"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

# Initialize processor
processor = CreateProcessor()


@router.post(
    "/",
    response_model=CreateResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Process prompt using C.R.E.A.T.E. framework",
    description="Enhance a prompt using the C.R.E.A.T.E. framework methodology",
)
async def process_prompt(request: CreateRequestModel) -> CreateResponseModel:
    """Process a prompt using the C.R.E.A.T.E. framework.

    Args:
        request: The create request containing prompt and options.

    Returns:
        CreateResponseModel containing the enhanced prompt and metadata.

    Raises:
        HTTPException: If processing fails or validation errors occur.
    """
    try:
        # Process the prompt
        response = await processor.process_prompt(
            input_prompt=request.input_prompt,
            domain=request.domain,
        )

        # Convert to API response model
        return CreateResponseModel(
            enhanced_prompt=response.enhanced_prompt,
            framework_components=response.framework_components,
            metadata=response.metadata,
            processing_time=response.processing_time,
            success=response.success,
            errors=response.errors,
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing error: {e}",
        ) from e


@router.get(
    "/health",
    response_model=HealthResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check the health status of the C.R.E.A.T.E. framework service",
)
async def health_check() -> HealthResponseModel:
    """Health check endpoint for the C.R.E.A.T.E. framework service.

    Returns:
        HealthResponseModel containing service health information.
    """
    return HealthResponseModel(
        status="healthy",
        service="promptcraft-hybrid-create-core",
        version="1.0.0",
        environment="development",
        debug=True,
        timestamp=time.time(),
    )


@router.get(
    "/domains",
    response_model=DomainResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Get available processing domains",
    description="Retrieve the list of available domains for prompt processing",
)
async def get_domains() -> DomainResponseModel:
    """Get available processing domains.

    Returns:
        DomainResponseModel containing available domains.
    """
    return DomainResponseModel(
        domains=["general", "technical", "legal", "business", "academic"],
        default_domain="general",
    )


@router.get(
    "/framework",
    response_model=FrameworkInfoResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Get C.R.E.A.T.E. framework information",
    description="Retrieve information about the C.R.E.A.T.E. framework",
)
async def get_framework_info() -> FrameworkInfoResponseModel:
    """Get C.R.E.A.T.E. framework information.

    Returns:
        FrameworkInfoResponseModel containing framework details.
    """
    return FrameworkInfoResponseModel(
        framework="C.R.E.A.T.E.",
        components=[
            "Context",
            "Request",
            "Examples",
            "Augmentations",
            "Tone & Format",
            "Evaluation",
        ],
        description="A comprehensive framework for prompt enhancement and optimization",
        version="1.0.0",
    )


# Error handlers
@router.exception_handler(ValidationError)
async def validation_error_handler(_request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors.

    Args:
        request: The request that caused the error.
        exc: The validation exception.

    Returns:
        JSONResponse with error details.
    """
    error_response = ErrorResponseModel(
        error="ValidationError",
        detail=str(exc),
        timestamp=time.time(),
        request_id=None,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump(),
    )


@router.exception_handler(Exception)
async def general_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle general errors.

    Args:
        request: The request that caused the error.
        exc: The exception.

    Returns:
        JSONResponse with error details.
    """
    error_response = ErrorResponseModel(
        error="InternalServerError",
        detail=f"An unexpected error occurred: {exc}",
        timestamp=time.time(),
        request_id=None,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )

"""
API response utilities for consistent JSON responses
"""

from flask import jsonify
from typing import Any, Dict, Optional, Union


def success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
    """
    Create standardized success response
    
    Args:
        data: Response data (optional)
        message: Success message (optional)
        
    Returns:
        Flask JSON response for success
    """
    response = {"success": True}
    
    if data is not None:
        response["data"] = data
        
    if message:
        response["message"] = message
        
    return jsonify(response)


def error_response(error: Union[str, Exception], status_code: int = 400, details: Dict = None) -> tuple:
    """
    Create standardized error response
    
    Args:
        error: Error message or exception
        status_code: HTTP status code
        details: Additional error details (optional)
        
    Returns:
        Tuple of (Flask JSON response, status code)
    """
    error_message = str(error) if not isinstance(error, str) else error
    
    response = {
        "success": False,
        "error": error_message
    }
    
    if details:
        response["details"] = details
        
    return jsonify(response), status_code


def validation_error_response(field_errors: Dict[str, str]) -> tuple:
    """
    Create standardized validation error response
    
    Args:
        field_errors: Dictionary mapping field names to error messages
        
    Returns:
        Tuple of (Flask JSON response, 400 status code)
    """
    return error_response(
        "Validation failed", 
        status_code=400,
        details={"field_errors": field_errors}
    )


def not_found_response(resource: str = "Resource") -> tuple:
    """
    Create standardized 404 response
    
    Args:
        resource: Name of the resource that wasn't found
        
    Returns:
        Tuple of (Flask JSON response, 404 status code)
    """
    return error_response(f"{resource} not found", status_code=404)


def server_error_response(error: Union[str, Exception]) -> tuple:
    """
    Create standardized 500 response
    
    Args:
        error: Error message or exception
        
    Returns:
        Tuple of (Flask JSON response, 500 status code)
    """
    return error_response(error, status_code=500)


def paginated_response(items: list, page: int, per_page: int, total: int, **kwargs) -> Dict[str, Any]:
    """
    Create standardized paginated response
    
    Args:
        items: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        **kwargs: Additional response data
        
    Returns:
        Flask JSON response with pagination info
    """
    import math
    
    total_pages = math.ceil(total / per_page) if per_page > 0 else 1
    
    response_data = {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
    
    # Add any additional data
    response_data.update(kwargs)
    
    return success_response(response_data)


class APIException(Exception):
    """
    Custom exception for API errors with status codes
    """
    
    def __init__(self, message: str, status_code: int = 400, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def handle_api_exception(error: APIException) -> tuple:
    """
    Handle APIException and convert to error response
    
    Args:
        error: APIException instance
        
    Returns:
        Tuple of (Flask JSON response, status code)
    """
    return error_response(error.message, error.status_code, error.details)


def require_fields(data: Dict, required_fields: list) -> None:
    """
    Validate that required fields are present in request data
    
    Args:
        data: Request data dictionary
        required_fields: List of required field names
        
    Raises:
        APIException: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        field_errors = {field: "This field is required" for field in missing_fields}
        raise APIException(
            f"Missing required fields: {', '.join(missing_fields)}",
            status_code=400,
            details={"field_errors": field_errors}
        )


def validate_tutorial_id(tutorial_id: str) -> None:
    """
    Validate tutorial ID format
    
    Args:
        tutorial_id: Tutorial ID to validate
        
    Raises:
        APIException: If tutorial ID is invalid
    """
    import re
    
    if not tutorial_id or not isinstance(tutorial_id, str):
        raise APIException("Invalid tutorial ID format", status_code=400)
    
    # Tutorial IDs should be alphanumeric with possible underscores/hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', tutorial_id):
        raise APIException("Tutorial ID contains invalid characters", status_code=400)
    
    if len(tutorial_id) < 3 or len(tutorial_id) > 50:
        raise APIException("Tutorial ID must be between 3 and 50 characters", status_code=400)
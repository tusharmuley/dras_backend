"""
Custom CORS Middleware to ensure CORS headers are always added.
This is a backup in case django-cors-headers doesn't work properly.
"""
from django.utils.deprecation import MiddlewareMixin


class CustomCorsMiddleware(MiddlewareMixin):
    """
    Custom middleware to add CORS headers to all responses.
    This ensures CORS works even if django-cors-headers fails.
    """
    
    def process_response(self, request, response):
        # Add CORS headers to all responses
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD'
        response['Access-Control-Allow-Headers'] = (
            'accept, accept-encoding, authorization, content-type, '
            'content-disposition, dnt, origin, user-agent, '
            'x-csrftoken, x-requested-with, x-forwarded-for, x-forwarded-proto'
        )
        response['Access-Control-Max-Age'] = '86400'
        response['Access-Control-Expose-Headers'] = 'content-type, content-length, authorization'
        
        # Handle preflight OPTIONS requests
        if request.method == 'OPTIONS':
            response.status_code = 200
            response.content = b''
        
        return response


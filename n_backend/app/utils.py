"""
Utility functions and decorators for admin authorization
"""
from functools import wraps
from django.http import JsonResponse
from n_backend.app.users.models import Users


def require_admin(view_func):
    """
    Decorator to require admin role for accessing a view.
    Expects Bearer token in Authorization header.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Import here to avoid circular import
        from n_backend.app.users.views import verify_simple_token
        
        # Check for Authorization header
        auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'success': False,
                'message': 'Authorization token required'
            }, status=401)
        
        # Verify token
        token = auth_header.split(' ', 1)[1].strip()
        payload = verify_simple_token(token)
        
        if not payload or not payload.get('user_id'):
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired token'
            }, status=401)
        
        # Check if user exists and is admin
        try:
            user = Users.objects.get(id=payload['user_id'])
            if user.role != 'admin':
                return JsonResponse({
                    'success': False,
                    'message': 'Admin access required'
                }, status=403)
        except Users.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
        
        # Add user to request for use in view
        request.user = user
        return view_func(request, *args, **kwargs)
    
    return wrapper


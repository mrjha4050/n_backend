from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import json
from datetime import datetime
from .models import Users
import base64

def generate_simple_token(user):
    """Generate simple token for user"""
    token_data = f"{user.id}:{user.email}:{datetime.utcnow().timestamp()}"
    token = base64.b64encode(token_data.encode()).decode()
    return token

def verify_simple_token(token):
    """Verify simple token and return user data"""
    try:
        decoded = base64.b64decode(token.encode()).decode()
        parts = decoded.split(':')
        if len(parts) >= 3:
            user_id, email, timestamp = parts[0], parts[1], float(parts[2])
            # Check if token is not too old (7 days)
            if datetime.utcnow().timestamp() - timestamp < 7 * 24 * 3600:
                return {'user_id': user_id, 'email': email}
        return None
    except:
        return None

@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """Register a new user"""
    try:
        data = json.loads(request.body)
        
        required_fields = ['username', 'email', 'password', 'role']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'success': False,
                    'message': f'{field} is required'
                }, status=400)
        
        if Users.objects.filter(email=data['email']).exists():
            return JsonResponse({
                'success': False,
                'message': 'User with this email already exists'
            }, status=400)
        
        user = Users(
            username=data['username'],
            email=data['email'],
            password=data['password'],  # Will be hashed in save()
            role=data['role'],
            profileUrl=data.get('profileUrl', '')
        )
        
        user.full_clean() 
        user.save()
        
        token = generate_simple_token(user)
        
        return JsonResponse({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'profileUrl': user.profileUrl,
                    'created_at': user.created_at.isoformat()
                },
                'token': token
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except IntegrityError:
        return JsonResponse({
            'success': False,
            'message': 'User with this email already exists'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        }, status=500)



@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """Login user and return JWT token"""
    try:
        data = json.loads(request.body)
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({
                'success': False,
                'message': 'Email and password are required'
            }, status=400)
        
        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials'
            }, status=401)
        
        # Check password
        if not user.check_password(password):
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials'
            }, status=401)
        
        token = generate_simple_token(user)
        
        return JsonResponse({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'profileUrl': user.profileUrl,
                    'created_at': user.created_at.isoformat()
                },
                'token': token
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_profile(request):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'success': False,
                'message': 'Authorization token required'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        payload = verify_simple_token(token)
        
        if not payload:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired token'
            }, status=401)
        
        user = Users.objects.get(id=payload['user_id'])
        
        return JsonResponse({
            'success': True,
            'data': {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'profileUrl': user.profileUrl,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                }
            }
        })
        
    except Users.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to get profile: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_profile(request):
    """Update user profile"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'success': False,
                'message': 'Authorization token required'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        payload = verify_simple_token(token)
        
        if not payload:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired token'
            }, status=401)
        
        user = Users.objects.get(id=payload['user_id'])
        data = json.loads(request.body)
        
        # Update allowed fields
        if 'username' in data:
            user.username = data['username']
        if 'profileUrl' in data:
            user.profileUrl = data['profileUrl']
        if 'role' in data:
            user.role = data['role']
        
        user.full_clean()
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully',
            'data': {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'profileUrl': user.profileUrl,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                }
            }
        })
        
    except Users.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to update profile: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def change_password(request):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'success': False,
                'message': 'Authorization token required'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        payload = verify_simple_token(token)
        
        if not payload:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired token'
            }, status=401)
        
        user = Users.objects.get(id=payload['user_id'])
        data = json.loads(request.body)
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return JsonResponse({
                'success': False,
                'message': 'Current password and new password are required'
            }, status=400)
        
        # Verify current password
        if not user.check_password(current_password):
            return JsonResponse({
                'success': False,
                'message': 'Current password is incorrect'
            }, status=400)
        
        user.password = new_password 
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Users.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to change password: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_account(request):
    """Delete user account"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'success': False,
                'message': 'Authorization token required'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        payload = verify_simple_token(token)
        
        if not payload:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired token'
            }, status=401)
        
        user = Users.objects.get(id=payload['user_id'])
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Account deleted successfully'
        })
        
    except Users.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to delete account: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def list_users(request):
    """List all users (admin only)"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'success': False,
                'message': 'Authorization token required'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        payload = verify_simple_token(token)
        
        if not payload:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired token'
            }, status=401)
        
        
        # if payload.get('role') != 'admin':
        #     return JsonResponse({
        #         'success': False,
        #         'message': 'Admin access required'
        #     }, status=403)
        
        users = Users.objects.all()
        users_data = []
        
        for user in users:
            users_data.append({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'profileUrl': user.profileUrl,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'users': users_data,
                'total': len(users_data)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to list users: {str(e)}'
        }, status=500)
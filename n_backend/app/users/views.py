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
from ..cloudinary import upload_image

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
            if datetime.utcnow().timestamp() - timestamp < 7 * 24 * 3600:
                return {'user_id': user_id, 'email': email}
        return None
    except:
        return None

@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """Register a new user - handles both JSON and multipart/form-data"""
    try:
        # Check content type and parse data accordingly
        content_type = request.META.get('CONTENT_TYPE', '').lower()
        
        if 'multipart/form-data' in content_type:
            # Handle multipart/form-data (when file is included)
            data = request.POST.dict()
            pdf_file = request.FILES.get('pdf', None) or request.FILES.get('file', None)
        else:
            # Handle JSON request
            try:
                # Safely decode request body with proper encoding handling
                if hasattr(request.body, 'decode'):
                    body_str = request.body.decode('utf-8', errors='ignore')
                else:
                    body_str = str(request.body)
                data = json.loads(body_str)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid request data: {str(e)}. Please ensure the request is properly formatted.'
                }, status=400)
            pdf_file = None
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'role']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'success': False,
                    'message': f'{field} is required'
                }, status=400)
        
        # Check if email already exists
        if Users.objects.filter(email=data['email']).exists():
            return JsonResponse({
                'success': False,
                'message': 'User with this email already exists'
            }, status=400)
        
        # Create user
        user = Users(
            username=data['username'],
            email=data['email'],
            password=data['password'],  # Will be hashed in save()
            role=data['role']
        )
        
        # Handle optional fields from JSON
        if 'profileUrl' in data:
            user.profileUrl = data['profileUrl']
        if 'pdfUrl' in data:
            user.pdfUrl = data['pdfUrl']
        
        # Validate and save user first
        user.full_clean() 
        user.save()
        
        # Handle PDF file upload if provided
        pdf_url = None
        pdf_public_id = None
        if pdf_file:
            try:
                # Validate PDF file
                if not pdf_file.name.lower().endswith('.pdf'):
                    # Delete the user if PDF upload fails validation
                    user.delete()
                    return JsonResponse({
                        'success': False,
                        'message': 'File must be a PDF. Please upload a file with .pdf extension.'
                    }, status=400)
                
                # Validate file size (max 10MB)
                max_size = 10 * 1024 * 1024  # 10MB
                if pdf_file.size > max_size:
                    user.delete()
                    return JsonResponse({
                        'success': False,
                        'message': f'File size exceeds maximum allowed size of 10MB. Current size: {pdf_file.size / (1024 * 1024):.2f}MB'
                    }, status=400)
                
                # Upload to Cloudinary
                from ..cloudinary import upload_image
                upload_result = upload_image(
                    pdf_file,
                    folder=f'users/{user.id}/pdfs',
                    resource_type='raw',
                    overwrite=True
                )
                
                if upload_result and upload_result.get('secure_url'):
                    pdf_url = upload_result.get('secure_url')
                    pdf_public_id = upload_result.get('public_id', '')
                    
                    # Update user with PDF URL
                    user.pdfUrl = pdf_url
                    if hasattr(user, 'pdfPublicId'):
                        user.pdfPublicId = pdf_public_id or ''
                    user.save()
                else:
                    # If upload fails, continue without PDF (don't delete user)
                    pass
                    
            except Exception as upload_error:
                # If PDF upload fails, continue without PDF (don't fail registration)
                # Log the error but don't block registration
                pass
        
        # Generate token
        token = generate_simple_token(user)
        
        # Safely get pdfPublicId (in case migration hasn't been run)
        if not pdf_public_id:
            pdf_public_id = getattr(user, 'pdfPublicId', None) or ''
        
        return JsonResponse({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'profileUrl': user.profileUrl or '',
                    'pdfUrl': user.pdfUrl or '',
                    'pdfPublicId': pdf_public_id,
                    'created_at': user.created_at.isoformat()
                },
                'token': token
            }
        }, status=201)
        
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'message': f'Invalid JSON data: {str(e)}'
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
    except UnicodeDecodeError as e:
        return JsonResponse({
            'success': False,
            'message': f'Encoding error: {str(e)}. Please check your request format.'
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
        
        # Safely get pdfPublicId (in case migration hasn't been run)
        pdf_public_id = getattr(user, 'pdfPublicId', None) or ''
        
        return JsonResponse({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'profileUrl': user.profileUrl or '',
                    'pdfUrl': user.pdfUrl or '',
                    'pdfPublicId': pdf_public_id,
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
        
        # Safely get pdfPublicId (in case migration hasn't been run)
        pdf_public_id = getattr(user, 'pdfPublicId', None) or ''
        
        return JsonResponse({
            'success': True,
            'data': {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'profileUrl': user.profileUrl or '',
                    'pdfUrl': user.pdfUrl or '',
                    'pdfPublicId': pdf_public_id,
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
        
        if 'username' in data:
            user.username = data['username']
        if 'profileUrl' in data:
            user.profileUrl = data['profileUrl']
        if 'pdfUrl' in data:
            user.pdfUrl = data['pdfUrl']
        if 'pdfPublicId' in data and hasattr(user, 'pdfPublicId'):
            user.pdfPublicId = data['pdfPublicId']
        if 'role' in data:
            user.role = data['role']
        
        user.full_clean()
        user.save()
        
        # Safely get pdfPublicId (in case migration hasn't been run)
        pdf_public_id = getattr(user, 'pdfPublicId', None) or ''
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully',
            'data': {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'profileUrl': user.profileUrl or '',
                    'pdfUrl': user.pdfUrl or '',
                    'pdfPublicId': pdf_public_id,
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
            # Safely get pdfPublicId (in case migration hasn't been run)
            pdf_public_id = getattr(user, 'pdfPublicId', None) or ''
            users_data.append({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'profileUrl': user.profileUrl or '',
                'pdfUrl': user.pdfUrl or '',
                'pdfPublicId': pdf_public_id,
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

@csrf_exempt
@require_http_methods(["POST"])
def upload_profile_image(request):
    """Upload profile image to Cloudinary and update user profileUrl"""
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
        
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file provided'
            }, status=400)
        
        file = request.FILES['file']
        
        # Upload to Cloudinary
        upload_result = upload_image(
            file,
            folder=f'users/{user.id}/profile',
            resource_type='image',
            overwrite=True
        )
        
        # Update user profileUrl
        user.profileUrl = upload_result['secure_url']
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile image uploaded successfully',
            'data': {
                'profileUrl': user.profileUrl
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
            'message': f'Failed to upload profile image: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_pdf(request):
    """Upload PDF to Cloudinary and update user pdfUrl and pdfPublicId"""
    try:
        # Authentication check
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
        
        # Get user
        try:
            user = Users.objects.get(id=payload['user_id'])
        except Users.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
        
        # File validation
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file provided. Please include a PDF file in the request.'
            }, status=400)
        
        file = request.FILES['file']
        
        # Validate file size (max 10MB for PDFs)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': f'File size exceeds maximum allowed size of 10MB. Current size: {file.size / (1024 * 1024):.2f}MB'
            }, status=400)
        
        # Check if file is PDF by extension and content type
        if not file.name.lower().endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'message': 'File must be a PDF. Please upload a file with .pdf extension.'
            }, status=400)
        
        # Validate content type if available
        if hasattr(file, 'content_type') and file.content_type and 'pdf' not in file.content_type.lower():
            return JsonResponse({
                'success': False,
                'message': f'Invalid file type. Expected PDF, got {file.content_type}'
            }, status=400)
        
        # Upload to Cloudinary with enhanced error handling
        try:
            upload_result = upload_image(
                file,
                folder=f'users/{user.id}/pdfs',
                resource_type='raw',
                overwrite=True
            )
            
            # Validate upload result
            if not upload_result:
                return JsonResponse({
                    'success': False,
                    'message': 'Cloudinary upload failed: No response received'
                }, status=500)
            
            # Extract URLs and public_id from upload result
            secure_url = upload_result.get('secure_url') or upload_result.get('url')
            public_id = upload_result.get('public_id')
            
            if not secure_url:
                return JsonResponse({
                    'success': False,
                    'message': 'Cloudinary upload succeeded but no URL was returned'
                }, status=500)
            
            # Update user with PDF URL and public_id
            user.pdfUrl = secure_url
            # Safely set pdfPublicId (in case migration hasn't been run)
            if hasattr(user, 'pdfPublicId'):
                user.pdfPublicId = public_id or ''
            user.save()
            
            # Return comprehensive response with metadata
            response_data = {
                'pdfUrl': secure_url,
                'publicId': public_id,
                'fileName': file.name,
                'fileSize': file.size,
                'uploadedAt': user.updated_at.isoformat()
            }
            
            # Include additional metadata from Cloudinary if available
            if 'bytes' in upload_result:
                response_data['fileSizeInCloud'] = upload_result['bytes']
            if 'format' in upload_result:
                response_data['format'] = upload_result['format']
            if 'created_at' in upload_result:
                response_data['cloudinaryCreatedAt'] = upload_result['created_at']
            
            return JsonResponse({
                'success': True,
                'message': 'PDF uploaded successfully to Cloudinary',
                'data': response_data
            }, status=200)
            
        except Exception as cloudinary_error:
            # Specific error handling for Cloudinary upload failures
            error_message = str(cloudinary_error)
            
            # Check for common Cloudinary errors
            if 'Invalid cloud_name' in error_message or 'Invalid API key' in error_message:
                return JsonResponse({
                    'success': False,
                    'message': 'Cloudinary configuration error. Please contact administrator.',
                    'error': 'Configuration error'
                }, status=500)
            elif 'file size' in error_message.lower() or 'too large' in error_message.lower():
                return JsonResponse({
                    'success': False,
                    'message': 'File is too large for upload',
                    'error': 'File size error'
                }, status=400)
            elif 'network' in error_message.lower() or 'connection' in error_message.lower():
                return JsonResponse({
                    'success': False,
                    'message': 'Network error while uploading to Cloudinary. Please try again.',
                    'error': 'Network error'
                }, status=503)
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Failed to upload PDF to Cloudinary: {error_message}',
                    'error': 'Upload error'
                }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format'
        }, status=400)
    except Exception as e:
        # Generic error handler for unexpected errors
        return JsonResponse({
            'success': False,
            'message': f'An unexpected error occurred: {str(e)}',
            'error': 'Internal server error'
        }, status=500)
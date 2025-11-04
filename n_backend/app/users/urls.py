from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/upload-image/', views.upload_profile_image, name='upload_profile_image'),
    path('profile/upload-pdf/', views.upload_pdf, name='upload_pdf'),
    path('change-password/', views.change_password, name='change_password'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('list/', views.list_users, name='list_users'),
    # Admin endpoints
    path('admin/counts/', views.get_user_counts, name='get_user_counts'),
]
    
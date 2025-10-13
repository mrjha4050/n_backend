
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('n_backend.app.users.urls')),
    path('api/articles/', include('n_backend.app.articles.urls')),
]

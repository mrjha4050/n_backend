from django.urls import path
from . import views


urlpatterns =[
    path('create/', views.create_article, name='create_article'),
    path('get/', views.get_article, name='get_article'),
    path('update/', views.update_article, name='update_article'),
    path('delete/', views.delete_article, name='delete_article'),
    path('get-by-id/', views.get_article_by_id, name='get_article_by_id'),
    path('get-by-category/', views.get_article_by_category, name='get_article_by_category'),
    path('get-by-author/', views.get_article_by_author, name='get_article_by_author'),
]
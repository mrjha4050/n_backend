from django.urls import path
from . import views


urlpatterns =[
    path('create/', views.create_article, name='create_article'),
    path('get/', views.get_articles, name='get_article'),
    path('update/', views.update_article, name='update_article'),
    path('delete/', views.delete_article, name='delete_article'),
    path('get-by-id/', views.get_article_by_id, name='get_article_by_id'),
    path('get-by-category/', views.get_articles_by_category, name='get_article_by_category'),
    path('get-by-author/', views.get_articles_by_author, name='get_article_by_author'),
    path('aggregate-counts/', views.article_comments_likes, name='article_counts'),
    # Interaction endpoints
    path('add-like/', views.add_like, name='add_like'),
    path('add-comment/', views.add_comment, name='add_comment'),
    path('get-comments/', views.get_comments, name='get_comments'),
    path('toggle-save-article/', views.toggle_save_article, name='toggle_save_article'),
    path('user-interaction/', views.get_user_interaction, name='user_interaction'),
    path('comments-likes/', views.article_comments_likes, name='article_comments_likes'),

# Cloudinary image upload endpoint
    path('upload-image/', views.upload_article_image, name='upload_article_image'),
]
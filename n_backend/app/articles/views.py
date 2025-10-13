from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Articles
from n_backend.app.users.models import Users

@require_http_methods(["POST"])
def create_article(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        article = Articles.objects.create(
            title=data['title'],
            content=data['content'],
            author=Users.objects.get(id=data['author']),
            media=data['media'],
            category=data['category'],
            published=data['published'],
            status=data['status']
        )
        return JsonResponse({'message': 'Article created successfully'}, status=201)
    return JsonResponse({'message': 'Invalid request method'}, status=405)


@require_http_methods(["GET"])
def get_article(request):
    if request.method == 'GET':
        articles = Articles.objects.all()
        return JsonResponse({'articles': articles}, status=200)
    return JsonResponse({'message': 'Invalid request method'}, status=405)


@require_http_methods(["PUT"])
def update_article(request):
    if request.method == 'PUT' or request.method == 'POST':
        data = json.loads(request.body)
        article = Articles.objects.get(id=data['id'])
        article.title = data['title']
        article.content = data['content']
        article.media = data['media']
        article.category = data['category']
        article.published = data['published']
        article.status = data['status']
        article.save()
        return JsonResponse({'message': 'Article updated successfully'}, status=200)


@require_http_methods(["DELETE"])
def delete_article(request):
    if request.method == 'DELETE':
        article = Articles.objects.get(id=request.GET.get('id'))
        article.delete()
        return JsonResponse({'message': 'Article deleted successfully'}, status=200)
    return JsonResponse({'message': 'Invalid request method'}, status=405)


@require_http_methods(["GET"])
def get_article_by_id(request):
    if request.method == 'GET':
        article = Articles.objects.get(id=request.GET.get('id'))
        return JsonResponse({'article': article}, status=200)
    return JsonResponse({'message': 'Invalid request method'}, status=405)

@require_http_methods(["GET"])
def get_article_by_category(request):
    if request.method == 'GET':
        articles = Articles.objects.filter(category=request.GET.get('category'))
        return JsonResponse({'articles': articles}, status=200)
    return JsonResponse({'message': 'Invalid request method'}, status=405)

@require_http_methods(["GET"])
def get_article_by_author(request):
    if request.method == 'GET':
        articles = Articles.objects.filter(author=request.GET.get('author'))
        return JsonResponse({'articles': articles}, status=200)
    return JsonResponse({'message': 'Invalid request method'}, status=405)


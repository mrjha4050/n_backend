# views.py (articles)
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q

from .models import Articles, ArticleInteraction
from n_backend.app.users.models import Users

# Adjust these imports to match where you keep them
from n_backend.app.users.views import verify_simple_token

try:
    from n_backend.app.cloudinary import upload_image
except Exception:
    def upload_image(file_obj, folder=None, resource_type='image', overwrite=False):
        raise Exception("upload_image not implemented or import path wrong")


def article_to_dict(article: Articles):
    """
    Convert Articles instance to JSON-serializable dict.
    Now includes likes_count and comments_count from ArticleInteraction model.
    """
    try:
        content = json.loads(article.content) if article.content else []
    except Exception:
        content = article.content or ""

    author_data = {}
    if article.author:
        author_data = {
            "id": str(article.author.id),
            "username": getattr(article.author, "username", ""),
            "email": getattr(article.author, "email", "")
        }

    # Calculate counts using ArticleInteraction model
    likes_count = ArticleInteraction.objects.filter(article=article, liked=True).count()
    comments_count = ArticleInteraction.objects.filter(
        article=article
    ).exclude(comment__isnull=True).exclude(comment='').count()

    return {
        "id": str(article.id),
        "title": article.title,
        "content": content,
        "author": author_data,
        "media": article.media or [],
        "category": article.category or "",
        "published": bool(article.published),
        "status": article.status or "",
        "likes_count": likes_count,
        "comments_count": comments_count,
        "created_at": article.created_at.isoformat() if article.created_at else None,
        "updated_at": article.updated_at.isoformat() if article.updated_at else None
    }


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def article_comments_likes(request):
    """
    Get likes and comments count for an article
    Expects JSON: {"article_id": "uuid"}
    """
    if request.method == "OPTIONS":
        return JsonResponse({}, status=200)

    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)

        article_id = data.get('article_id')
        if not article_id:
            return JsonResponse({"success": False, "message": "article_id required"}, status=400)

        try:
            article = Articles.objects.get(id=article_id)
        except Articles.DoesNotExist:
            return JsonResponse({"success": False, "message": "Article not found"}, status=404)

        # Calculate counts using ArticleInteraction model
        likes_count = ArticleInteraction.objects.filter(article=article, liked=True).count()
        comments_count = ArticleInteraction.objects.filter(
            article=article
        ).exclude(comment__isnull=True).exclude(comment='').count()

        return JsonResponse({
            "success": True,
            "data": {
                "article_id": str(article.id),
                "likes_count": likes_count,
                "comments_count": comments_count
            }
        }, status=200)

    except Exception as e:
        print("article_comments_likes exception:", str(e))
        return JsonResponse({"success": False, "message": f"Failed to get counts: {str(e)}"}, status=500)
# Update the add_like function
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def add_like(request):
    """
    Add/remove a like to an article using ArticleInteraction model
    Expects JSON: {"article_id": "uuid", "user_id": "uuid"} (or "userid")
    """
    if request.method == "OPTIONS":
        return JsonResponse({}, status=200)

    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)

        article_id = data.get('article_id')
        # Handle both 'user_id' and 'userid' for compatibility
        user_id = data.get('user_id') or data.get('userid')

        if not article_id or not user_id:
            return JsonResponse({"success": False, "message": "article_id and user_id required"}, status=400)

        try:
            article = Articles.objects.get(id=article_id)
            user = Users.objects.get(id=user_id)
        except (Articles.DoesNotExist, Users.DoesNotExist):
            return JsonResponse({"success": False, "message": "Article or User not found"}, status=404)

        # Get or create interaction for this user and article
        interaction, created = ArticleInteraction.objects.get_or_create(
            article=article,
            user=user,
            defaults={'liked': True}
        )

        if not created:
            # Toggle like status if interaction already exists
            interaction.liked = not interaction.liked
            interaction.save()

        action = "liked" if interaction.liked else "unliked"

        # Get updated likes count
        likes_count = ArticleInteraction.objects.filter(article=article, liked=True).count()

        return JsonResponse({
            "success": True,
            "message": f"Article {action} successfully",
            "data": {
                "article_id": str(article.id),
                "liked": interaction.liked,
                "likes_count": likes_count
            }
        }, status=200)

    except Exception as e:
        print("add_like exception:", str(e))
        return JsonResponse({"success": False, "message": f"Failed to toggle like: {str(e)}"}, status=500)



@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def add_comment(request):
    """
    Add a comment to an article using ArticleInteraction model
    Expects JSON: {"article_id": "uuid", "user_id": "uuid", "comment": "comment text"}
    """
    if request.method == "OPTIONS":
        return JsonResponse({}, status=200)

    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)

        article_id = data.get('article_id')
        # Handle both 'user_id' and 'user_d' (frontend typo)
        user_id = data.get('user_id') or data.get('user_d')
        comment_text = data.get('comment', '').strip()

        if not article_id or not user_id:
            return JsonResponse({"success": False, "message": "article_id and user_id required"}, status=400)

        if not comment_text:
            return JsonResponse({"success": False, "message": "Comment text is required"}, status=400)

        try:
            article = Articles.objects.get(id=article_id)
            user = Users.objects.get(id=user_id)
        except (Articles.DoesNotExist, Users.DoesNotExist):
            return JsonResponse({"success": False, "message": "Article or User not found"}, status=404)

        # Get or create interaction for this user and article
        # Use update_or_create to handle existing interactions
        interaction, created = ArticleInteraction.objects.update_or_create(
            article=article,
            user=user,
            defaults={
                'comment': comment_text,
                # Don't change like/save status when adding comment
            }
        )

        # If the interaction already existed, update the comment
        if not created:
            interaction.comment = comment_text
            interaction.save()

        # Get updated comments count
        comments_count = ArticleInteraction.objects.filter(
            article=article
        ).exclude(comment__isnull=True).exclude(comment='').count()

        return JsonResponse({
            "success": True,
            "message": "Comment added successfully",
            "data": {
                "article_id": str(article.id),
                "comment_id": str(interaction.id),
                "comment": comment_text,
                "comments_count": comments_count
            }
        }, status=201)

    except Exception as e:
        print("add_comment exception:", str(e))
        return JsonResponse({"success": False, "message": f"Failed to add comment: {str(e)}"}, status=500)

@require_http_methods(["GET"])
def get_comments(request):
    """
    Get all comments for an article using ArticleInteraction model
    Query param: article_id
    """
    try:
        article_id = request.GET.get("article_id")
        if not article_id:
            return JsonResponse({"success": False, "message": "article_id required"}, status=400)

        try:
            article = Articles.objects.get(id=article_id)
        except Articles.DoesNotExist:
            return JsonResponse({"success": False, "message": "Article not found"}, status=404)

        # Get only interactions that have comments
        comments = ArticleInteraction.objects.filter(
            article=article
        ).exclude(comment__isnull=True).exclude(comment='').order_by("-created_at")

        comments_data = []
        for interaction in comments:
            comments_data.append({
                "id": str(interaction.id),
                "comment": interaction.comment,
                "liked": interaction.liked,
                "saved": interaction.saved,
                "author": {
                    "id": str(interaction.user.id),
                    "username": getattr(interaction.user, "username", ""),
                    "email": getattr(interaction.user, "email", "")
                } if interaction.user else {},
                "created_at": interaction.created_at.isoformat() if interaction.created_at else None
            })

        return JsonResponse({
            "success": True,
            "data": {
                "article_id": str(article.id),
                "comments": comments_data,
                "comments_count": len(comments_data)
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Failed to fetch comments: {str(e)}"}, status=500)

# Update the toggle_save_article function
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def toggle_save_article(request):
    """
    Toggle save status for an article
    Expects JSON: {"article_id": "uuid", "user_id": "uuid"} (or "userid")
    """
    if request.method == "OPTIONS":
        return JsonResponse({}, status=200)

    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)

        article_id = data.get('article_id')
        # Handle both 'user_id' and 'userid' for compatibility
        user_id = data.get('user_id') or data.get('userid')

        if not article_id or not user_id:
            return JsonResponse({"success": False, "message": "article_id and user_id required"}, status=400)

        try:
            article = Articles.objects.get(id=article_id)
            user = Users.objects.get(id=user_id)
        except (Articles.DoesNotExist, Users.DoesNotExist):
            return JsonResponse({"success": False, "message": "Article or User not found"}, status=404)

        # Get or create interaction for this user and article
        interaction, created = ArticleInteraction.objects.get_or_create(
            article=article,
            user=user,
            defaults={'saved': True}
        )

        if not created:
            # Toggle save status if interaction already exists
            interaction.saved = not interaction.saved
            interaction.save()

        action = "saved" if interaction.saved else "unsaved"

        return JsonResponse({
            "success": True,
            "message": f"Article {action} successfully",
            "data": {
                "article_id": str(article.id),
                "saved": interaction.saved
            }
        }, status=200)

    except Exception as e:
        print("toggle_save_article exception:", str(e))
        return JsonResponse({"success": False, "message": f"Failed to toggle save: {str(e)}"}, status=500)

@require_http_methods(["GET"])
def get_user_interaction(request):
    """
    Get user's interaction with an article (like, save status)
    Query params: article_id, user_id
    """
    try:
        article_id = request.GET.get("article_id")
        user_id = request.GET.get("user_id")

        if not article_id or not user_id:
            return JsonResponse({"success": False, "message": "article_id and user_id required"}, status=400)

        try:
            interaction = ArticleInteraction.objects.get(article_id=article_id, user_id=user_id)
            interaction_data = {
                "liked": interaction.liked,
                "saved": interaction.saved,
                "has_comment": bool(interaction.comment and interaction.comment.strip())
            }
        except ArticleInteraction.DoesNotExist:
            interaction_data = {
                "liked": False,
                "saved": False,
                "has_comment": False
            }

        return JsonResponse({
            "success": True,
            "data": interaction_data
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Failed to fetch user interaction: {str(e)}"}, status=500)


# Your existing functions (create_article, get_articles, update_article, delete_article, etc.)
# remain mostly the same but now use the updated article_to_dict

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def create_article(request):
    """
    Accepts:
      - JSON: application/json body: { title, content (array or JSON-string), category, tags(optional), media(optional) }
      - multipart/form-data: 'title', 'content' (JSON string), files named file_0, file_1 ... for image blocks
    Auth:
      - If Authorization: Bearer <token> present and valid, the token-user will be used as author.
      - Otherwise, the request may include 'author' id in payload (useful for tests).
    Frontend convention:
      - Image blocks referencing files use value 'file_<index>' and corresponding request.FILES contains that file.
    """
    if request.method == "OPTIONS":
        return JsonResponse({}, status=200)

    try:
        # Try to authenticate with token if present
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
        author_user = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            payload = verify_simple_token(token)
            if payload and payload.get("user_id"):
                try:
                    author_user = Users.objects.get(id=payload["user_id"])
                except Users.DoesNotExist:
                    return JsonResponse({"success": False, "message": "Token user not found"}, status=401)

        content_type = (request.META.get("CONTENT_TYPE") or "").lower()

        # Read fields depending on content type
        if "multipart/form-data" in content_type:
            title = (request.POST.get("title") or "").strip()
            content_raw = request.POST.get("content") or ""
            category = request.POST.get("category") or ""
            tags_raw = request.POST.get("tags")
            # media may be provided directly
            media_raw = request.POST.get("media")
        else:
            # JSON payload
            try:
                body_text = request.body.decode("utf-8") if request.body else ""
                if not body_text:
                    return JsonResponse({"success": False, "message": "Empty request body"}, status=400)
                body_json = json.loads(body_text)
            except Exception as e:
                return JsonResponse({"success": False, "message": f"Invalid JSON body: {str(e)}"}, status=400)

            title = (body_json.get("title") or "").strip()
            content_field = body_json.get("content", "")
            # normalize content_raw to string that can be json.loads later
            if isinstance(content_field, (list, dict)):
                content_raw = json.dumps(content_field)
            else:
                content_raw = content_field or ""
            category = body_json.get("category", "") or ""
            tags_raw = body_json.get("tags")
            media_raw = body_json.get("media")

            # If no token-authenticated author, allow author id in JSON payload
            if not author_user and body_json.get("author"):
                try:
                    author_user = Users.objects.get(id=body_json.get("author"))
                except Users.DoesNotExist:
                    return JsonResponse({"success": False, "message": "Author id provided but user not found"},
                                        status=400)

        if not title:
            return JsonResponse({"success": False, "message": "Title is required"}, status=400)
        if not content_raw:
            return JsonResponse({"success": False, "message": "Content is required"}, status=400)

        # If still no author, error
        if not author_user:
            return JsonResponse({"success": False, "message": "Author not specified and token not provided"},
                                status=401)

        # Parse content JSON
        try:
            content_list = json.loads(content_raw) if isinstance(content_raw, str) else content_raw
            if not isinstance(content_list, list):
                return JsonResponse({"success": False, "message": "Content must be a JSON array of blocks"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Invalid content JSON: {str(e)}"}, status=400)

        # Process image blocks and upload files for any 'file_<i>' references
        processed_content = []
        media_urls = media_raw if isinstance(media_raw, list) else []
        if not isinstance(media_urls, list):
            try:
                media_urls = json.loads(media_raw) if media_raw else []
            except Exception:
                media_urls = []

        for idx, block in enumerate(content_list):
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "paragraph":
                processed_content.append({"type": "paragraph", "value": block.get("value", "")})
                continue
            if btype == "image":
                val = block.get("value", "")
                caption = block.get("caption", "")
                # If value refers to a file key
                if isinstance(val, str) and val.startswith("file_") and val in request.FILES:
                    file_obj = request.FILES.get(val)
                    try:
                        upload_result = upload_image(file_obj, folder=f"articles/{author_user.id}",
                                                     resource_type="image", overwrite=True)
                        uploaded_url = upload_result.get("secure_url") or upload_result.get("url")
                        if uploaded_url:
                            media_urls.append(uploaded_url)
                            processed_content.append({"type": "image", "value": uploaded_url, "caption": caption})
                        else:
                            processed_content.append({"type": "image", "value": "", "caption": caption})
                    except Exception as ue:
                        print("upload_image error:", ue)
                        processed_content.append({"type": "image", "value": "", "caption": caption})
                else:
                    # direct URL or empty
                    if isinstance(val, str) and val:
                        media_urls.append(val)
                    processed_content.append({"type": "image", "value": val or "", "caption": caption})
                continue
            # unknown types are preserved
            processed_content.append(block)

        # Save article
        article = Articles(
            title=title,
            content=json.dumps(processed_content),
            author=author_user,
            media=media_urls,
            category=category or "",
            published=False,
            status="draft"
        )

        article.full_clean()
        article.save()

        return JsonResponse(
            {"success": True, "message": "Article created", "data": {"article": article_to_dict(article)}}, status=201)

    except ValidationError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
    except IntegrityError:
        return JsonResponse({"success": False, "message": "Integrity error while creating article"}, status=400)
    except Exception as e:
        print("create_article exception:", str(e))
        return JsonResponse({"success": False, "message": f"Failed to create article: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_articles(request):
    """
    Get all articles
    """
    try:
        qs = Articles.objects.all().order_by("-created_at")
        data = [article_to_dict(a) for a in qs]
        return JsonResponse({"success": True, "data": {"articles": data, "total": len(data)}}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Failed to fetch articles: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["PUT", "POST"])
def update_article(request):
    """
    Accepts JSON body with:
      - id (required), fields to update: title, content (array or JSON string), category, media, published, status
    """
    try:
        try:
            body_text = request.body.decode("utf-8") if request.body else ""
            data = json.loads(body_text)
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Invalid JSON body: {str(e)}"}, status=400)

        article_id = data.get("id")
        if not article_id:
            return JsonResponse({"success": False, "message": "Article id is required"}, status=400)

        try:
            article = Articles.objects.get(id=article_id)
        except Articles.DoesNotExist:
            return JsonResponse({"success": False, "message": "Article not found"}, status=404)

        # Update fields
        if "title" in data:
            article.title = data.get("title") or article.title
        if "content" in data:
            content_field = data.get("content")
            if isinstance(content_field, (list, dict)):
                article.content = json.dumps(content_field)
            else:
                article.content = content_field or article.content
        if "media" in data:
            article.media = data.get("media") or article.media
        if "category" in data:
            article.category = data.get("category") or article.category
        if "published" in data:
            article.published = bool(data.get("published"))
        if "status" in data:
            article.status = data.get("status") or article.status

        article.full_clean()
        article.save()
        return JsonResponse(
            {"success": True, "message": "Article updated", "data": {"article": article_to_dict(article)}}, status=200)

    except ValidationError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
    except Exception as e:
        print("update_article exception:", str(e))
        return JsonResponse({"success": False, "message": f"Failed to update article: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_article(request):
    try:
        # allow id as query param or JSON body
        article_id = request.GET.get("id")
        if not article_id:
            try:
                body_text = request.body.decode("utf-8") if request.body else ""
                data = json.loads(body_text) if body_text else {}
                article_id = data.get("id")
            except Exception:
                article_id = None

        if not article_id:
            return JsonResponse({"success": False, "message": "Article id required"}, status=400)

        try:
            article = Articles.objects.get(id=article_id)
        except Articles.DoesNotExist:
            return JsonResponse({"success": False, "message": "Article not found"}, status=404)

        article.delete()
        return JsonResponse({"success": True, "message": "Article deleted"}, status=200)

    except Exception as e:
        print("delete_article exception:", str(e))
        return JsonResponse({"success": False, "message": f"Failed to delete article: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_article_by_id(request):
    try:
        article_id = request.GET.get("id")
        if not article_id:
            return JsonResponse({"success": False, "message": "Article id required"}, status=400)
        try:
            article = Articles.objects.get(id=article_id)
        except Articles.DoesNotExist:
            return JsonResponse({"success": False, "message": "Article not found"}, status=404)
        return JsonResponse({"success": True, "data": {"article": article_to_dict(article)}}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Failed to fetch article: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_articles_by_category(request):
    """
    Get articles by category
    """
    try:
        category = request.GET.get("category")
        if category is None:
            return JsonResponse({"success": False, "message": "Category required"}, status=400)
        qs = Articles.objects.filter(category=category).order_by("-created_at")
        data = [article_to_dict(a) for a in qs]
        return JsonResponse({"success": True, "data": {"articles": data, "total": len(data)}}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Failed to fetch articles: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_articles_by_author(request):
    """
    Get articles by author
    """
    try:
        author_id = request.GET.get("author")
        if not author_id:
            return JsonResponse({"success": False, "message": "Author id required"}, status=400)
        qs = Articles.objects.filter(author=author_id).order_by("-created_at")
        data = [article_to_dict(a) for a in qs]
        return JsonResponse({"success": True, "data": {"articles": data, "total": len(data)}}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Failed to fetch articles: {str(e)}"}, status=500)
"""
Test script for Admin Endpoints
Run this script to test all admin functionality:
    python test_admin_endpoints.py

Make sure:
1. Django server is running (python manage.py runserver)
2. You have an admin user created (see script below)
3. Database migrations are applied
"""

import os
import sys
import django
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'n_backend.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from n_backend.app.users.models import Users
from n_backend.app.articles.models import Articles
from n_backend.app.users.views import generate_simple_token, verify_simple_token
import requests

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/articles"
AUTH_BASE = f"{BASE_URL}/auth"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response, description):
    print(f"\n{description}:")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data
    except:
        print(f"Response: {response.text}")
        return None

def create_test_admin_user():
    """Create or get an admin user for testing"""
    print_section("Creating Test Admin User")
    
    email = "admin@test.com"
    username = "test_admin"
    password = "admin123"
    
    try:
        user = Users.objects.get(email=email)
        print(f"Admin user already exists: {user.email} (role: {user.role})")
        if user.role != 'admin':
            print(f"Updating role to 'admin'...")
            user.role = 'admin'
            user.save()
    except Users.DoesNotExist:
        print(f"Creating new admin user: {email}")
        user = Users.objects.create(
            username=username,
            email=email,
            password=password,  # Will be hashed in save()
            role='admin'
        )
        print(f"Admin user created: {user.email} (role: {user.role})")
    
    return user

def create_test_articles(admin_user):
    """Create some test articles with different statuses"""
    print_section("Creating Test Articles")
    
    # Create a regular user (journalist) to be the author
    try:
        journalist = Users.objects.get(email="journalist@test.com")
    except Users.DoesNotExist:
        journalist = Users.objects.create(
            username="test_journalist",
            email="journalist@test.com",
            password="test123",
            role="journalist"
        )
        print(f"Created journalist user: {journalist.email}")
    
    # Create draft articles (pending)
    draft_articles = []
    for i in range(3):
        try:
            article = Articles.objects.create(
                title=f"Test Draft Article {i+1}",
                content=json.dumps([
                    {"type": "paragraph", "value": f"This is test draft article {i+1} content."}
                ]),
                author=journalist,
                category="Technology",
                published=False,
                status="draft"
            )
            draft_articles.append(article)
            print(f"Created draft article: {article.title} (ID: {article.id})")
        except Exception as e:
            print(f"Error creating draft article: {e}")
    
    return draft_articles

def test_admin_endpoints():
    """Test all admin endpoints"""
    
    # Step 1: Create admin user
    admin_user = create_test_admin_user()
    admin_token = generate_simple_token(admin_user)
    print(f"\nAdmin Token: {admin_token[:50]}...")
    
    # Step 2: Create test articles
    test_articles = create_test_articles(admin_user)
    
    if not test_articles:
        print("No test articles created. Creating at least one...")
        try:
            journalist = Users.objects.filter(role='journalist').first()
            if not journalist:
                journalist = Users.objects.create(
                    username="test_journalist",
                    email="journalist@test.com",
                    password="test123",
                    role="journalist"
                )
            article = Articles.objects.create(
                title="Test Draft Article",
                content=json.dumps([{"type": "paragraph", "value": "Test content"}]),
                author=journalist,
                published=False,
                status="draft"
            )
            test_articles = [article]
        except Exception as e:
            print(f"Error: {e}")
            return
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Get User Counts
    print_section("Test 1: Get User Counts")
    try:
        response = requests.get(f"{AUTH_BASE}/admin/counts/", headers=headers)
        counts_data = print_response(response, "GET /auth/admin/counts/")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Django server is running: python manage.py runserver")
        return
    
    # Test 2: Get Pending Articles
    print_section("Test 2: Get Pending Articles")
    try:
        response = requests.get(f"{API_BASE}/admin/pending/", headers=headers)
        pending_data = print_response(response, "GET /api/articles/admin/pending/")
    except Exception as e:
        print(f"Error: {e}")
        return
    
    if pending_data and pending_data.get('success') and pending_data.get('data', {}).get('articles'):
        articles = pending_data['data']['articles']
        if articles:
            first_article_id = articles[0]['id']
            
            # Test 3: Approve Single Article
            print_section("Test 3: Approve Single Article")
            try:
                response = requests.post(
                    f"{API_BASE}/admin/approve/",
                    headers=headers,
                    json={"article_id": first_article_id}
                )
                print_response(response, "POST /api/articles/admin/approve/ (single)")
            except Exception as e:
                print(f"Error: {e}")
            
            # Test 4: Reject Article (if we have another one)
            if len(articles) > 1:
                second_article_id = articles[1]['id']
                print_section("Test 4: Reject Article")
                try:
                    response = requests.post(
                        f"{API_BASE}/admin/reject/",
                        headers=headers,
                        json={"article_id": second_article_id}
                    )
                    print_response(response, "POST /api/articles/admin/reject/")
                except Exception as e:
                    print(f"Error: {e}")
            
            # Test 5: Bulk Approve (create some more drafts first)
            print_section("Test 5: Bulk Approve Articles")
            try:
                # Create a few more draft articles
                journalist = Users.objects.filter(role='journalist').first()
                bulk_article_ids = []
                for i in range(2):
                    article = Articles.objects.create(
                        title=f"Bulk Test Article {i+1}",
                        content=json.dumps([{"type": "paragraph", "value": f"Bulk test {i+1}"}]),
                        author=journalist,
                        published=False,
                        status="draft"
                    )
                    bulk_article_ids.append(str(article.id))
                
                response = requests.post(
                    f"{API_BASE}/admin/approve/",
                    headers=headers,
                    json={"article_ids": bulk_article_ids}
                )
                print_response(response, "POST /api/articles/admin/approve/ (bulk)")
            except Exception as e:
                print(f"Error: {e}")
            
            # Test 6: Delete Article (admin)
            print_section("Test 6: Delete Article (Admin)")
            try:
                # Create an article to delete
                journalist = Users.objects.filter(role='journalist').first()
                article_to_delete = Articles.objects.create(
                    title="Article to Delete",
                    content=json.dumps([{"type": "paragraph", "value": "This will be deleted"}]),
                    author=journalist,
                    published=False,
                    status="draft"
                )
                
                response = requests.delete(
                    f"{API_BASE}/admin/delete/",
                    headers=headers,
                    params={"id": str(article_to_delete.id)}
                )
                print_response(response, "DELETE /api/articles/admin/delete/")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("No pending articles found to test with")
    else:
        print("Failed to get pending articles or no articles found")
    
    # Test 7: Test with non-admin user (should fail)
    print_section("Test 7: Test Admin Endpoint with Non-Admin User")
    try:
        # Get or create a regular user
        try:
            regular_user = Users.objects.filter(role='reader').first()
            if not regular_user:
                regular_user = Users.objects.create(
                    username="test_reader",
                    email="reader@test.com",
                    password="test123",
                    role="reader"
                )
        except Exception as e:
            print(f"Error creating regular user: {e}")
            return
        
        regular_token = generate_simple_token(regular_user)
        regular_headers = {
            "Authorization": f"Bearer {regular_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{AUTH_BASE}/admin/counts/", headers=regular_headers)
        print_response(response, "GET /auth/admin/counts/ (should fail with 403)")
    except Exception as e:
        print(f"Error: {e}")
    
    print_section("Testing Complete!")
    print("\nSummary:")
    print("✅ All admin endpoints have been tested")
    print("✅ Check the responses above to verify they work correctly")
    print("\nNote: Make sure Django server is running on http://localhost:8000")

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library is required.")
        print("Install it with: pip install requests")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("  ADMIN ENDPOINTS TEST SCRIPT")
    print("="*60)
    print("\nMake sure Django server is running:")
    print("  python manage.py runserver")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    test_admin_endpoints()


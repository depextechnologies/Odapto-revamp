"""
Test suite for Template System in Odapto
Tests template categories (admin), publishing templates, and template gallery
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "odapto.admin@emergent.com"
ADMIN_PASSWORD = "SecurePassword123!"

class TestTemplateSystem:
    """Template System endpoint tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated admin session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert data.get("role") == "admin", "User is not admin"
        
        # Set auth token
        if "session_token" in data:
            session.headers.update({"Authorization": f"Bearer {data['session_token']}"})
        
        return session

    # ============== Template Categories Tests ==============
    
    def test_get_template_categories(self, admin_session):
        """GET /api/template-categories - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/template-categories")
        assert response.status_code == 200
        
        categories = response.json()
        assert isinstance(categories, list)
        print(f"✓ Found {len(categories)} template categories")
        
        # Check for expected categories
        category_names = [c.get("name") for c in categories]
        assert "Project Management" in category_names, "Project Management category not found"
        print(f"✓ Categories: {category_names}")
    
    def test_create_template_category(self, admin_session):
        """POST /api/template-categories - admin only"""
        # Create a test category
        response = admin_session.post(f"{BASE_URL}/api/template-categories", json={
            "name": "TEST_Marketing_Category",
            "description": "Templates for marketing teams"
        })
        assert response.status_code == 200
        
        category = response.json()
        assert category.get("name") == "TEST_Marketing_Category"
        assert category.get("description") == "Templates for marketing teams"
        assert "category_id" in category
        print(f"✓ Created category: {category['name']} (ID: {category['category_id']})")
        
        # Store for cleanup
        self._test_category_id = category["category_id"]
    
    def test_create_category_unauthorized(self):
        """POST /api/template-categories - should fail without admin auth"""
        response = requests.post(f"{BASE_URL}/api/template-categories", json={
            "name": "Unauthorized Category",
            "description": "Should not be created"
        })
        # Should return 401 (not authenticated) or 403 (forbidden)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthorized category creation blocked (status: {response.status_code})")
    
    def test_delete_template_category(self, admin_session):
        """DELETE /api/template-categories/{id} - admin only"""
        # First create a category to delete
        create_response = admin_session.post(f"{BASE_URL}/api/template-categories", json={
            "name": "TEST_Delete_Category",
            "description": "Will be deleted"
        })
        assert create_response.status_code == 200
        category_id = create_response.json()["category_id"]
        
        # Delete the category
        response = admin_session.delete(f"{BASE_URL}/api/template-categories/{category_id}")
        assert response.status_code == 200
        print(f"✓ Deleted category: {category_id}")
        
        # Verify deletion
        categories = requests.get(f"{BASE_URL}/api/template-categories").json()
        assert not any(c["category_id"] == category_id for c in categories)
        print(f"✓ Verified category is removed from list")

    # ============== Templates Gallery Tests ==============
    
    def test_get_templates(self):
        """GET /api/templates - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200
        
        templates = response.json()
        assert isinstance(templates, list)
        print(f"✓ Found {len(templates)} templates")
        
        if len(templates) > 0:
            # Verify template structure
            template = templates[0]
            assert "board_id" in template
            assert template.get("is_template") == True
            assert "template_name" in template
            assert "list_count" in template
            assert "card_count" in template
            print(f"✓ Template structure verified: {template['template_name']}")
    
    def test_get_templates_with_category_filter(self):
        """GET /api/templates?category_id=xxx - filter by category"""
        # Get all categories first
        categories = requests.get(f"{BASE_URL}/api/template-categories").json()
        if len(categories) > 0:
            category_id = categories[0]["category_id"]
            
            response = requests.get(f"{BASE_URL}/api/templates?category_id={category_id}")
            assert response.status_code == 200
            
            templates = response.json()
            # All returned templates should be in this category
            for t in templates:
                assert t.get("template_category_id") == category_id
            print(f"✓ Category filter works: {len(templates)} templates in category {categories[0]['name']}")
    
    def test_get_template_detail(self):
        """GET /api/templates/{id} - get template with lists/cards preview"""
        # Get a template ID first
        templates = requests.get(f"{BASE_URL}/api/templates").json()
        if len(templates) > 0:
            template_id = templates[0]["board_id"]
            
            response = requests.get(f"{BASE_URL}/api/templates/{template_id}")
            assert response.status_code == 200
            
            template = response.json()
            assert template.get("board_id") == template_id
            assert "lists" in template
            assert isinstance(template["lists"], list)
            
            # Check if lists have cards
            if len(template["lists"]) > 0:
                assert "cards" in template["lists"][0]
                print(f"✓ Template detail with {len(template['lists'])} lists loaded")
    
    def test_get_nonexistent_template(self):
        """GET /api/templates/{invalid_id} - should return 404"""
        response = requests.get(f"{BASE_URL}/api/templates/invalid_template_id")
        assert response.status_code == 404
        print("✓ 404 returned for nonexistent template")

    # ============== Publish Template Tests ==============
    
    def test_publish_board_as_template(self, admin_session):
        """POST /api/boards/{id}/publish-template - privileged users only"""
        # Get admin's boards first
        workspaces = admin_session.get(f"{BASE_URL}/api/workspaces").json()
        if len(workspaces) > 0:
            workspace_id = workspaces[0]["workspace_id"]
            boards = admin_session.get(f"{BASE_URL}/api/workspaces/{workspace_id}/boards").json()
            
            if len(boards) > 0:
                board_id = boards[0]["board_id"]
                
                # Get a category
                categories = requests.get(f"{BASE_URL}/api/template-categories").json()
                assert len(categories) > 0, "No categories available for publishing"
                category_id = categories[0]["category_id"]
                
                # Publish as template
                response = admin_session.post(f"{BASE_URL}/api/boards/{board_id}/publish-template", json={
                    "template_name": "TEST_Published_Template",
                    "template_description": "Testing template publishing",
                    "category_id": category_id
                })
                assert response.status_code == 200, f"Publish failed: {response.text}"
                
                template = response.json()
                assert template.get("is_template") == True
                assert template.get("template_name") == "TEST_Published_Template"
                print(f"✓ Board published as template: {template['board_id']}")
                
                # Store for cleanup
                self._test_template_id = template["board_id"]

    # ============== Use Template Tests ==============
    
    def test_use_template(self, admin_session):
        """POST /api/templates/{id}/use - create board from template"""
        # Get a template
        templates = requests.get(f"{BASE_URL}/api/templates").json()
        if len(templates) > 0:
            template_id = templates[0]["board_id"]
            
            # Get workspace
            workspaces = admin_session.get(f"{BASE_URL}/api/workspaces").json()
            if len(workspaces) > 0:
                workspace_id = workspaces[0]["workspace_id"]
                
                response = admin_session.post(f"{BASE_URL}/api/templates/{template_id}/use", json={
                    "workspace_id": workspace_id,
                    "board_name": "TEST_Board_From_Template"
                })
                assert response.status_code == 200, f"Use template failed: {response.text}"
                
                board = response.json()
                assert board.get("name") == "TEST_Board_From_Template"
                assert board.get("is_template") == False
                assert board.get("created_from_template") == template_id
                print(f"✓ Board created from template: {board['board_id']}")
                
                # Store for cleanup
                self._test_board_id = board["board_id"]

    # ============== Cleanup ==============
    
    def test_cleanup_test_data(self, admin_session):
        """Cleanup test-created data"""
        # Delete test category
        categories = requests.get(f"{BASE_URL}/api/template-categories").json()
        for cat in categories:
            if cat["name"].startswith("TEST_"):
                admin_session.delete(f"{BASE_URL}/api/template-categories/{cat['category_id']}")
                print(f"✓ Deleted test category: {cat['name']}")
        
        # Note: Test templates and boards are left for manual cleanup if needed
        print("✓ Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

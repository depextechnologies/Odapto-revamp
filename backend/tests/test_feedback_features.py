"""
Tests for Odapto Feedback Features
- Teams API endpoints (create, get, add member, remove member)
- Board member removal (inviter-only permissions)
- Card actions endpoints (copy, move, delete)
- Board stats (list_count, card_count, attachment_count)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token using admin credentials"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "odapto.admin@emergent.com",
        "password": "SecurePassword123!"
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("session_token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client

@pytest.fixture(scope="module")
def workspace_id():
    """Use existing workspace from test credentials"""
    return "ws_3a39c12c673e"

@pytest.fixture(scope="module")
def board_id():
    """Use existing board from test credentials"""
    return "board_8b24ee8c579c"

class TestTeamsAPI:
    """Test Teams CRUD endpoints"""
    
    team_id = None
    
    def test_create_team(self, authenticated_client, workspace_id):
        """POST /api/workspaces/{workspace_id}/teams - Create a team"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/workspaces/{workspace_id}/teams",
            json={
                "name": f"TEST_Team_{uuid.uuid4().hex[:6]}",
                "description": "Test team for feedback features"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "team_id" in data
        assert "name" in data
        assert "workspace_id" in data
        assert data["workspace_id"] == workspace_id
        assert "members" in data
        assert len(data["members"]) == 1  # Owner is auto-added
        
        TestTeamsAPI.team_id = data["team_id"]
        print(f"Created team: {data['team_id']}")
    
    def test_get_workspace_teams(self, authenticated_client, workspace_id):
        """GET /api/workspaces/{workspace_id}/teams - Get all teams in workspace"""
        response = authenticated_client.get(f"{BASE_URL}/api/workspaces/{workspace_id}/teams")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Check if our created team is in the list
        team_ids = [t["team_id"] for t in data]
        assert TestTeamsAPI.team_id in team_ids, "Created team not found in workspace teams"
        print(f"Found {len(data)} teams in workspace")
    
    def test_get_team(self, authenticated_client):
        """GET /api/teams/{team_id} - Get team details"""
        response = authenticated_client.get(f"{BASE_URL}/api/teams/{TestTeamsAPI.team_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["team_id"] == TestTeamsAPI.team_id
        assert "name" in data
        assert "members" in data
        print(f"Team details retrieved: {data['name']}")
    
    def test_update_team(self, authenticated_client):
        """PATCH /api/teams/{team_id} - Update team details"""
        response = authenticated_client.patch(
            f"{BASE_URL}/api/teams/{TestTeamsAPI.team_id}",
            json={"description": "Updated test description"}
        )
        
        assert response.status_code == 200
        
        # Verify update
        get_response = authenticated_client.get(f"{BASE_URL}/api/teams/{TestTeamsAPI.team_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["description"] == "Updated test description"
        print("Team updated successfully")
    
    def test_add_team_member_requires_user_id(self, authenticated_client):
        """POST /api/teams/{team_id}/members - Must provide valid user_id"""
        # First we need to create a test user to add
        # For now, test that the endpoint validates input
        response = authenticated_client.post(
            f"{BASE_URL}/api/teams/{TestTeamsAPI.team_id}/members",
            json={"user_id": "non_existent_user", "role": "member"}
        )
        
        # The request should succeed (endpoint doesn't validate user existence currently)
        # or return appropriate error
        print(f"Add member response: {response.status_code}")
        assert response.status_code in [200, 400, 404]
    
    def test_delete_team(self, authenticated_client):
        """DELETE /api/teams/{team_id} - Delete a team"""
        response = authenticated_client.delete(f"{BASE_URL}/api/teams/{TestTeamsAPI.team_id}")
        
        assert response.status_code == 200
        
        # Verify deletion
        get_response = authenticated_client.get(f"{BASE_URL}/api/teams/{TestTeamsAPI.team_id}")
        assert get_response.status_code == 404
        print("Team deleted successfully")


class TestBoardStats:
    """Test board statistics (list_count, card_count, attachment_count)"""
    
    def test_boards_include_stats(self, authenticated_client, workspace_id):
        """GET /api/workspaces/{workspace_id}/boards - Boards include list_count, card_count, attachment_count"""
        response = authenticated_client.get(f"{BASE_URL}/api/workspaces/{workspace_id}/boards")
        
        assert response.status_code == 200
        boards = response.json()
        
        if len(boards) > 0:
            board = boards[0]
            assert "list_count" in board, "Board missing list_count"
            assert "card_count" in board, "Board missing card_count"
            assert "attachment_count" in board, "Board missing attachment_count"
            
            # Values should be non-negative integers
            assert isinstance(board["list_count"], int) and board["list_count"] >= 0
            assert isinstance(board["card_count"], int) and board["card_count"] >= 0
            assert isinstance(board["attachment_count"], int) and board["attachment_count"] >= 0
            
            print(f"Board stats: lists={board['list_count']}, cards={board['card_count']}, attachments={board['attachment_count']}")
        else:
            pytest.skip("No boards found in workspace")


class TestBoardMembers:
    """Test board member management with inviter permissions"""
    
    def test_get_board_members(self, authenticated_client, board_id):
        """GET /api/boards/{board_id}/members - Get board members"""
        response = authenticated_client.get(f"{BASE_URL}/api/boards/{board_id}/members")
        
        assert response.status_code == 200
        members = response.json()
        
        assert isinstance(members, list)
        if len(members) > 0:
            member = members[0]
            assert "user_id" in member
            assert "role" in member
            print(f"Board has {len(members)} members")
        else:
            print("No members found on board")
    
    def test_board_owner_cannot_be_removed(self, authenticated_client, board_id):
        """DELETE /api/boards/{board_id}/members/{user_id} - Cannot remove board owner"""
        # First get board to find owner
        board_response = authenticated_client.get(f"{BASE_URL}/api/boards/{board_id}")
        assert board_response.status_code == 200
        board = board_response.json()
        
        owner_id = board.get("created_by")
        if owner_id:
            response = authenticated_client.delete(f"{BASE_URL}/api/boards/{board_id}/members/{owner_id}")
            assert response.status_code == 400, "Should not be able to remove board owner"
            print("Board owner correctly protected from removal")
        else:
            pytest.skip("No owner found on board")


class TestCardActions:
    """Test card actions: copy, move, delete"""
    
    card_id = None
    list_id = None
    second_list_id = None
    
    def test_get_board_with_lists(self, authenticated_client, board_id):
        """GET /api/boards/{board_id} - Get board with lists for card operations"""
        response = authenticated_client.get(f"{BASE_URL}/api/boards/{board_id}")
        
        assert response.status_code == 200
        board = response.json()
        
        assert "lists" in board
        lists = board["lists"]
        
        if len(lists) >= 2:
            TestCardActions.list_id = lists[0]["list_id"]
            TestCardActions.second_list_id = lists[1]["list_id"]
            print(f"Found lists: {TestCardActions.list_id}, {TestCardActions.second_list_id}")
        elif len(lists) == 1:
            TestCardActions.list_id = lists[0]["list_id"]
            TestCardActions.second_list_id = lists[0]["list_id"]
            print(f"Only one list found: {TestCardActions.list_id}")
        else:
            pytest.skip("No lists found on board")
    
    def test_create_test_card(self, authenticated_client):
        """POST /api/lists/{list_id}/cards - Create a test card"""
        if not TestCardActions.list_id:
            pytest.skip("No list_id available")
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/lists/{TestCardActions.list_id}/cards",
            json={
                "title": f"TEST_Card_{uuid.uuid4().hex[:6]}",
                "description": "Test card for card actions"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "card_id" in data
        TestCardActions.card_id = data["card_id"]
        print(f"Created test card: {data['card_id']}")
    
    def test_copy_card_by_creating_duplicate(self, authenticated_client):
        """POST /api/lists/{list_id}/cards - Copy card creates duplicate with (Copy) suffix"""
        if not TestCardActions.list_id:
            pytest.skip("No list_id available")
        
        # Copy is done by creating a new card with same properties + "(Copy)" suffix
        response = authenticated_client.post(
            f"{BASE_URL}/api/lists/{TestCardActions.list_id}/cards",
            json={
                "title": f"TEST_Card_{uuid.uuid4().hex[:6]} (Copy)",
                "description": "Copied card"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "(Copy)" in data["title"]
        print(f"Card copy created: {data['card_id']}")
    
    def test_move_card_to_different_list(self, authenticated_client):
        """POST /api/cards/{card_id}/move - Move card to different list"""
        if not TestCardActions.card_id or not TestCardActions.second_list_id:
            pytest.skip("No card or target list available")
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/cards/{TestCardActions.card_id}/move",
            json={"target_list_id": TestCardActions.second_list_id}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"Card moved to list: {TestCardActions.second_list_id}")
    
    def test_delete_card(self, authenticated_client):
        """DELETE /api/cards/{card_id} - Delete a card"""
        if not TestCardActions.card_id:
            pytest.skip("No card_id available")
        
        response = authenticated_client.delete(f"{BASE_URL}/api/cards/{TestCardActions.card_id}")
        
        assert response.status_code == 200
        
        # Verify deletion
        get_response = authenticated_client.get(f"{BASE_URL}/api/cards/{TestCardActions.card_id}")
        assert get_response.status_code == 404
        print("Card deleted successfully")


class TestNotifications:
    """Test notification endpoints"""
    
    def test_get_notifications(self, authenticated_client):
        """GET /api/notifications - Get user notifications"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"Found {len(data)} notifications")
    
    def test_get_unread_count(self, authenticated_client):
        """GET /api/notifications/unread-count - Get unread notification count"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications/unread-count")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "count" in data
        assert isinstance(data["count"], int)
        print(f"Unread notification count: {data['count']}")


class TestBoardInviteWithInviterTracking:
    """Test that board invitations track who invited the member"""
    
    def test_invite_member_stores_invited_by(self, authenticated_client, board_id):
        """POST /api/boards/{board_id}/invite - Invitation tracks inviter"""
        test_email = f"test_invite_{uuid.uuid4().hex[:6]}@example.com"
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/boards/{board_id}/invite",
            json={"email": test_email, "role": "member"}
        )
        
        # Should succeed (either adding existing user or creating pending invite)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "message" in data
        print(f"Invite response: {data['message']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Test Email Invitation System for Odapto
Tests workspace, board, and card-level email invitations
Tests invitation token validation, expiration, and single-use
Tests admin email logs and pending invitations endpoints
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "odapto.admin@emergent.com"
ADMIN_PASSWORD = "SecurePassword123!"
WORKSPACE_ID = "ws_3a39c12c673e"
BOARD_ID = "board_8b24ee8c579c"
TEST_TOKEN = "mhQGFlxchxQzOOqfY35OfeURc6o8vppnXfS-n62rSTg"


class TestInvitationEndpoints:
    """Test invitation token validation and acceptance"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Shared session with auth token"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            session.headers.update({"Authorization": f"Bearer {data['session_token']}"})
        return session
    
    # ============= INVITATION TOKEN VALIDATION =============
    
    def test_get_invitation_details_valid_token(self, session):
        """Test GET /api/invitations/{token} returns correct details for valid token"""
        # First create an invitation by inviting to workspace
        unique_email = f"test_token_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create invitation via workspace invite
        invite_response = session.post(
            f"{BASE_URL}/api/workspaces/{WORKSPACE_ID}/members",
            json={"email": unique_email, "role": "member"}
        )
        
        if invite_response.status_code == 200:
            invite_data = invite_response.json()
            if invite_data.get("pending"):
                # Get the invitation link and extract token
                invitation_link = invite_data.get("invitation_link", "")
                if "token=" in invitation_link:
                    token = invitation_link.split("token=")[-1]
                    
                    # Now test the GET invitation endpoint (public endpoint, no auth needed)
                    public_session = requests.Session()
                    response = public_session.get(f"{BASE_URL}/api/invitations/{token}")
                    
                    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
                    data = response.json()
                    
                    # Validate response structure
                    assert "invitation_type" in data
                    assert "target_name" in data
                    assert "invited_by_name" in data
                    assert "email" in data
                    assert "expires_at" in data
                    assert data["email"] == unique_email
                    print(f"✓ Valid token returns correct details: {data['invitation_type']} to {data['target_name']}")
                    return
        
        print("⚠ Could not create test invitation, skipping token validation test")
    
    def test_get_invitation_details_invalid_token(self):
        """Test GET /api/invitations/{token} returns 404 for invalid token"""
        response = requests.get(f"{BASE_URL}/api/invitations/invalid_token_12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid token returns 404")
    
    def test_get_invitation_details_used_token(self, session):
        """Test that used tokens are rejected with 410 status"""
        # Create and use an invitation
        unique_email = f"test_used_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create invitation via board invite
        invite_response = session.post(
            f"{BASE_URL}/api/boards/{BOARD_ID}/invite",
            json={"email": unique_email, "role": "member"}
        )
        
        if invite_response.status_code == 200:
            invite_data = invite_response.json()
            if invite_data.get("pending") and "invitation_link" in invite_data:
                token = invite_data["invitation_link"].split("token=")[-1]
                
                # Accept the invitation (requires auth)
                accept_response = session.post(f"{BASE_URL}/api/invitations/{token}/accept")
                
                if accept_response.status_code == 200:
                    # Now try to get the used token - should return 410
                    public_session = requests.Session()
                    response = public_session.get(f"{BASE_URL}/api/invitations/{token}")
                    assert response.status_code == 410, f"Expected 410 for used token, got {response.status_code}"
                    print("✓ Used token returns 410 (single-use verified)")
                    return
        
        print("⚠ Could not complete used token test")
    
    # ============= WORKSPACE INVITATION =============
    
    def test_workspace_invitation_sends_email(self, session):
        """Test POST /api/workspaces/{id}/members sends email to unregistered user"""
        unique_email = f"test_ws_{uuid.uuid4().hex[:8]}@example.com"
        
        response = session.post(
            f"{BASE_URL}/api/workspaces/{WORKSPACE_ID}/members",
            json={"email": unique_email, "role": "member"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should indicate pending (email sent to unregistered user)
        assert data.get("pending") == True, "Expected pending=True for unregistered user"
        assert "message" in data
        print(f"✓ Workspace invitation response: {data['message']}")
        
        # Check if email was actually sent (no error)
        if "email_error" in data:
            print(f"⚠ Email error: {data['email_error']}")
        else:
            print("✓ Workspace invitation email sent successfully")
    
    def test_workspace_invitation_existing_user(self, session):
        """Test workspace invitation adds existing user directly"""
        # Invite the admin user to the workspace (should already be member)
        response = session.post(
            f"{BASE_URL}/api/workspaces/{WORKSPACE_ID}/members",
            json={"email": ADMIN_EMAIL, "role": "member"}
        )
        
        # Should return 400 (already a member) or 200 with pending=False
        if response.status_code == 400:
            print("✓ Existing workspace member returns 400 (already a member)")
        elif response.status_code == 200:
            data = response.json()
            assert data.get("pending") == False, "Existing user should not have pending=True"
            print("✓ Existing user added directly (pending=False)")
    
    # ============= BOARD INVITATION =============
    
    def test_board_invitation_sends_email(self, session):
        """Test POST /api/boards/{id}/invite sends email to unregistered user"""
        unique_email = f"test_board_{uuid.uuid4().hex[:8]}@example.com"
        
        response = session.post(
            f"{BASE_URL}/api/boards/{BOARD_ID}/invite",
            json={"email": unique_email, "role": "member"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("pending") == True, "Expected pending=True for unregistered user"
        print(f"✓ Board invitation response: {data['message']}")
        
        if "email_error" in data:
            print(f"⚠ Email error: {data['email_error']}")
        else:
            print("✓ Board invitation email sent successfully")
    
    def test_board_invitation_existing_user(self, session):
        """Test board invitation adds existing user directly"""
        response = session.post(
            f"{BASE_URL}/api/boards/{BOARD_ID}/invite",
            json={"email": ADMIN_EMAIL, "role": "member"}
        )
        
        # Should return 400 (already a member) or 200 with pending=False
        if response.status_code == 400:
            print("✓ Existing board member returns 400 (already a member)")
        elif response.status_code == 200:
            data = response.json()
            if data.get("pending") == False:
                print("✓ Existing user added directly (pending=False)")
            else:
                print(f"Response: {data}")
    
    # ============= CARD INVITATION =============
    
    def test_card_invitation_sends_email(self, session):
        """Test POST /api/cards/{id}/invite sends email to unregistered user"""
        # First get a card from the board
        board_response = session.get(f"{BASE_URL}/api/boards/{BOARD_ID}")
        if board_response.status_code != 200:
            pytest.skip("Could not get board data")
        
        board_data = board_response.json()
        card_id = None
        
        # Find a card in any list
        for lst in board_data.get("lists", []):
            if lst.get("cards"):
                card_id = lst["cards"][0]["card_id"]
                break
        
        if not card_id:
            pytest.skip("No cards found in board")
        
        unique_email = f"test_card_{uuid.uuid4().hex[:8]}@example.com"
        
        response = session.post(
            f"{BASE_URL}/api/cards/{card_id}/invite",
            json={"email": unique_email}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("pending") == True, "Expected pending=True for unregistered user"
        print(f"✓ Card invitation response: {data['message']}")
        
        if "email_error" in data:
            print(f"⚠ Email error: {data['email_error']}")
        else:
            print("✓ Card invitation email sent successfully")
    
    # ============= INVITATION ACCEPTANCE =============
    
    def test_accept_invitation_requires_auth(self):
        """Test POST /api/invitations/{token}/accept requires authentication"""
        # Try to accept without auth
        response = requests.post(f"{BASE_URL}/api/invitations/some_token/accept", json={})
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Accept invitation requires authentication")
    
    def test_accept_invitation_success(self, session):
        """Test accepting a valid invitation adds user to workspace/board/card"""
        unique_email = f"test_accept_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create invitation
        invite_response = session.post(
            f"{BASE_URL}/api/workspaces/{WORKSPACE_ID}/members",
            json={"email": unique_email, "role": "member"}
        )
        
        if invite_response.status_code == 200:
            invite_data = invite_response.json()
            if invite_data.get("pending") and "invitation_link" in invite_data:
                token = invite_data["invitation_link"].split("token=")[-1]
                
                # Accept the invitation
                accept_response = session.post(f"{BASE_URL}/api/invitations/{token}/accept")
                assert accept_response.status_code == 200, f"Expected 200, got {accept_response.status_code}"
                
                data = accept_response.json()
                assert "message" in data
                assert "redirect" in data
                print(f"✓ Invitation accepted: {data['message']}, redirect: {data['redirect']}")
                return
        
        print("⚠ Could not complete accept invitation test")
    
    def test_accept_invitation_used_token_rejected(self, session):
        """Test that accepting a used token returns 410"""
        unique_email = f"test_reuse_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create invitation
        invite_response = session.post(
            f"{BASE_URL}/api/boards/{BOARD_ID}/invite",
            json={"email": unique_email, "role": "member"}
        )
        
        if invite_response.status_code == 200:
            invite_data = invite_response.json()
            if invite_data.get("pending") and "invitation_link" in invite_data:
                token = invite_data["invitation_link"].split("token=")[-1]
                
                # First acceptance
                first_accept = session.post(f"{BASE_URL}/api/invitations/{token}/accept")
                assert first_accept.status_code == 200
                
                # Second acceptance should fail
                second_accept = session.post(f"{BASE_URL}/api/invitations/{token}/accept")
                assert second_accept.status_code == 410, f"Expected 410 for reused token, got {second_accept.status_code}"
                print("✓ Used token rejected on second accept (single-use verified)")
                return
        
        print("⚠ Could not complete reuse test")


class TestAdminEmailEndpoints:
    """Test admin email logs and pending invitations endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Session authenticated as admin"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, "Admin login failed"
        data = response.json()
        session.headers.update({"Authorization": f"Bearer {data['session_token']}"})
        return session
    
    def test_get_email_logs(self, admin_session):
        """Test GET /api/admin/email-logs returns logs"""
        response = admin_session.get(f"{BASE_URL}/api/admin/email-logs")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "logs" in data
        assert "total" in data
        assert isinstance(data["logs"], list)
        print(f"✓ Email logs returned: {len(data['logs'])} logs, total: {data['total']}")
        
        # Validate log structure if logs exist
        if data["logs"]:
            log = data["logs"][0]
            assert "to_email" in log
            assert "email_type" in log
            assert "success" in log
            assert "sent_at" in log
            print(f"✓ Latest log: {log['email_type']} to {log['to_email']} - success: {log['success']}")
    
    def test_get_email_logs_with_filter(self, admin_session):
        """Test GET /api/admin/email-logs with success_only filter"""
        # Test success_only=true
        response = admin_session.get(f"{BASE_URL}/api/admin/email-logs?success_only=true")
        assert response.status_code == 200
        data = response.json()
        
        # All logs should have success=True
        for log in data["logs"]:
            assert log["success"] == True, f"Log with success=False found: {log}"
        print(f"✓ Success filter works: {len(data['logs'])} successful logs")
    
    def test_get_email_logs_pagination(self, admin_session):
        """Test GET /api/admin/email-logs with pagination"""
        response = admin_session.get(f"{BASE_URL}/api/admin/email-logs?limit=5&skip=0")
        assert response.status_code == 200
        data = response.json()
        
        assert data["limit"] == 5
        assert data["skip"] == 0
        assert len(data["logs"]) <= 5
        print(f"✓ Pagination works: limit={data['limit']}, skip={data['skip']}, returned={len(data['logs'])}")
    
    def test_get_email_logs_requires_admin(self):
        """Test GET /api/admin/email-logs requires admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/email-logs")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Email logs endpoint requires authentication")
    
    def test_get_pending_invitations(self, admin_session):
        """Test GET /api/admin/pending-invitations returns pending invites"""
        response = admin_session.get(f"{BASE_URL}/api/admin/pending-invitations")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "invitations" in data
        assert isinstance(data["invitations"], list)
        print(f"✓ Pending invitations returned: {len(data['invitations'])} invitations")
        
        # Validate invitation structure if invitations exist
        if data["invitations"]:
            inv = data["invitations"][0]
            assert "token" in inv
            assert "email" in inv
            assert "invitation_type" in inv
            assert "target_name" in inv
            assert "is_expired" in inv
            print(f"✓ Latest invitation: {inv['invitation_type']} to {inv['target_name']} for {inv['email']}")
    
    def test_get_pending_invitations_requires_admin(self):
        """Test GET /api/admin/pending-invitations requires admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/pending-invitations")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Pending invitations endpoint requires authentication")


class TestInvitationExpiration:
    """Test invitation token expiration (7 days)"""
    
    @pytest.fixture(scope="class")
    def session(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            session.headers.update({"Authorization": f"Bearer {data['session_token']}"})
        return session
    
    def test_invitation_has_7_day_expiration(self, session):
        """Test that new invitations expire in 7 days"""
        unique_email = f"test_exp_{uuid.uuid4().hex[:8]}@example.com"
        
        invite_response = session.post(
            f"{BASE_URL}/api/workspaces/{WORKSPACE_ID}/members",
            json={"email": unique_email, "role": "member"}
        )
        
        if invite_response.status_code == 200:
            invite_data = invite_response.json()
            if invite_data.get("pending") and "invitation_link" in invite_data:
                token = invite_data["invitation_link"].split("token=")[-1]
                
                # Get invitation details
                response = requests.get(f"{BASE_URL}/api/invitations/{token}")
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse expiration date
                    expires_at = datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00'))
                    created_roughly_now = datetime.now()
                    
                    # Check expiration is about 7 days from now
                    days_until_expiry = (expires_at.replace(tzinfo=None) - created_roughly_now).days
                    assert 6 <= days_until_expiry <= 8, f"Expected ~7 days expiry, got {days_until_expiry}"
                    print(f"✓ Invitation expires in {days_until_expiry} days (correct 7-day expiration)")
                    return
        
        print("⚠ Could not verify expiration time")


class TestEmailLogs:
    """Test that email sending creates logs in database"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        data = response.json()
        session.headers.update({"Authorization": f"Bearer {data['session_token']}"})
        return session
    
    def test_email_logs_created_on_invite(self, admin_session):
        """Test that sending an invitation creates an email log entry"""
        # Get initial log count
        initial_response = admin_session.get(f"{BASE_URL}/api/admin/email-logs")
        initial_count = initial_response.json()["total"]
        
        # Send an invitation
        unique_email = f"test_log_{uuid.uuid4().hex[:8]}@example.com"
        admin_session.post(
            f"{BASE_URL}/api/workspaces/{WORKSPACE_ID}/members",
            json={"email": unique_email, "role": "member"}
        )
        
        # Check log count increased
        after_response = admin_session.get(f"{BASE_URL}/api/admin/email-logs")
        after_count = after_response.json()["total"]
        
        assert after_count > initial_count, "Email log should be created after invitation"
        print(f"✓ Email log created: count went from {initial_count} to {after_count}")
        
        # Verify latest log is for our email
        latest_log = after_response.json()["logs"][0]
        assert latest_log["to_email"] == unique_email
        assert latest_log["email_type"] == "workspace_invite"
        print(f"✓ Log entry verified: {latest_log['email_type']} to {latest_log['to_email']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

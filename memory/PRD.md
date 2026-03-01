# Odapto - Kanban Work Management SaaS

## Project Overview
Odapto is a production-grade Kanban-based work management SaaS similar to Trello, built with React + FastAPI + MongoDB.

## Original Problem Statement
Build Odapto with:
- React frontend (Web-first with responsive tablet support)
- FastAPI backend with MongoDB
- Email/Password + Google OAuth authentication
- WebSockets for real-time collaboration
- Local file storage for attachments
- Role-based access control (Admin, Privileged, Normal)
- Workspace and board management
- Template system for reusable board templates
- Admin panel for user management and analytics

## User Personas

### Admin User
- Full system access
- Can manage all users and roles
- Can create/manage template categories
- View platform analytics and email logs
- First registered user becomes admin

### Privileged User
- Can create workspaces and boards
- Can publish boards as templates
- Access to template gallery

### Normal User
- Can create workspaces and boards
- Can use templates from gallery
- Cannot publish templates

## Core Requirements (Static)
1. **Authentication**: Email/password + Google OAuth via Emergent Auth
2. **Role-based Access**: Admin, Privileged, Normal user roles
3. **Workspaces**: Multi-workspace support with member management
4. **Kanban Boards**: Drag-and-drop lists and cards
5. **Card Features**: Description, due dates, labels, checklists, comments
6. **Templates**: Public template gallery with categories
7. **Admin Panel**: User management, analytics, category management
8. **Email Invitations**: Gmail SMTP for workspace/board/card invitations

## What's Been Implemented

### Backend (FastAPI)
- [x] Email/Password registration and login
- [x] Google OAuth via Emergent Auth integration
- [x] JWT-like session management with tokens
- [x] Role-based access control middleware
- [x] Workspace CRUD with member management
- [x] Board CRUD with background colors AND images
- [x] Board member invitation with notifications
- [x] List CRUD with position management
- [x] Card CRUD with full features (labels, due dates, checklists, comments)
- [x] Card move between lists endpoint
- [x] Card-level member invitation
- [x] Pending invites for unregistered users
- [x] **Gmail SMTP Email Service** (NEW - Mar 1)
- [x] **Secure invitation tokens with 7-day expiration** (NEW - Mar 1)
- [x] **Single-use invitation token validation** (NEW - Mar 1)
- [x] **Email logs with success/failure tracking** (NEW - Mar 1)
- [x] **Admin email logs endpoint** (NEW - Mar 1)
- [x] **Admin pending invitations endpoint** (NEW - Mar 1)
- [x] Comment notifications to board members
- [x] Notification system (create, read, mark read)
- [x] Template categories (admin only)
- [x] Board to template publishing (privileged users)
- [x] Template gallery with category filtering
- [x] Use template to create board
- [x] Global search across boards/cards/templates
- [x] Admin analytics endpoint
- [x] WebSocket endpoint for real-time collaboration
- [x] File upload for card attachments and board backgrounds

### Frontend (React)
- [x] Landing page with Odapto branding
- [x] Login/Register pages with Google OAuth
- [x] Dashboard with workspace listing and notification bell
- [x] Workspace page with board grid
- [x] Kanban board with drag-drop (hello-pangea/dnd)
- [x] Board member management and invitation
- [x] Board background color/image customization
- [x] Enhanced card preview with:
  - [x] Due date color-coding (red=overdue, orange=today, gray=future)
  - [x] Priority badges (Low/Medium/High/Urgent)
  - [x] Named labels with colors
  - [x] Assigned member avatars
  - [x] Attachment count
- [x] Enhanced card detail modal with:
  - [x] Labels section with named labels
  - [x] Assigned Members with card-level invitations
  - [x] Due Date picker with status indicator
  - [x] Priority selector (Low/Medium/High/Urgent)
  - [x] Description textarea
  - [x] Attachments with upload
  - [x] Checklist with progress bar
  - [x] Comments section
- [x] **Invitation Accept Page** (NEW - Mar 1)
  - [x] Shows invitation details (workspace/board/card name, inviter, role, expiration)
  - [x] Login/SignUp buttons for unauthenticated users
  - [x] Accept button for authenticated users
  - [x] Redirect handling for invitation flow
- [x] Template gallery page
- [x] Admin panel with user/category management and analytics
- [x] Profile page
- [x] Real-time notification system
- [x] Dark/Light theme support
- [x] Session persistence (localStorage + cookies)
- [x] Toast notifications (sonner)

### Email System
- [x] Gmail SMTP integration with STARTTLS
- [x] Branded email templates with Odapto colors
- [x] Workspace invitation emails
- [x] Board invitation emails
- [x] Card assignment emails
- [x] Invitation token generation and validation
- [x] 7-day token expiration
- [x] Single-use token enforcement
- [x] Email send logging (success/failure)
- [x] Retry mechanism (3 attempts)

### Design
- Odapto branding with logo colors (Orange #E67E4C, Teal #3A8B84)
- Outfit font for headings, Inter for body
- Clean enterprise-grade UI
- Responsive tablet-friendly design

## Prioritized Backlog

### P0 (Critical - COMPLETED)
- [x] Card-level member invitations
- [x] Invite unregistered users via email (pending invite system)
- [x] Due date color-coding on card previews
- [x] Named labels in card modal
- [x] Priority selector in card modal
- [x] Attachments section in card modal
- [x] Gmail SMTP email invitations
- [x] Secure invitation tokens

### P1 (High Priority - Next)
1. WebSocket integration for real-time board updates
2. Card activity/history log
3. Board filters (by label, due date, member)
4. Keyboard shortcuts
5. Card cover images

### P2 (Medium Priority)
1. Board export (JSON/CSV)
2. Card attachments preview
3. Checklist progress visualization on card preview
4. Board templates preview before use
5. User avatar upload
6. Email notifications for due dates

### Future (Subscription-Ready)
1. Subscription tiers (Free, Pro, Enterprise)
2. Premium templates
3. Feature flags system
4. Workspace-based billing
5. Advanced analytics dashboard
6. Microsoft OAuth

## Technical Architecture

### Stack
- **Frontend**: React 18, Tailwind CSS, Shadcn UI, @hello-pangea/dnd
- **Backend**: FastAPI, Motor (async MongoDB), bcrypt, httpx
- **Database**: MongoDB
- **Auth**: Session tokens + Emergent Google OAuth
- **Email**: Gmail SMTP (smtp.gmail.com:587 with STARTTLS)
- **Storage**: Local file storage (MVP), ready for S3 migration

### Key API Endpoints
All endpoints prefixed with `/api`:
- `/api/auth/*` - Authentication
- `/api/workspaces/*` - Workspace management
- `/api/boards/*` - Board operations
- `/api/lists/*` - List operations
- `/api/cards/*` - Card operations
- `/api/cards/{card_id}/invite` - Card-level member invitation
- `/api/cards/{card_id}/members/{member_id}` - Remove card member
- `/api/invitations/{token}` - Get invitation details (public)
- `/api/invitations/{token}/accept` - Accept invitation (auth required)
- `/api/templates` - Template gallery
- `/api/template-categories` - Admin category management
- `/api/admin/*` - Admin operations
- `/api/admin/email-logs` - Email send logs
- `/api/admin/pending-invitations` - Pending invitation tokens
- `/api/search` - Global search
- `/ws/board/{board_id}` - WebSocket for real-time

### Database Schema
- **users**: user_id, email, password_hash, name, role, picture
- **workspaces**: workspace_id, name, description, owner_id, members
- **boards**: board_id, workspace_id, name, background, background_type, members, is_template
- **lists**: list_id, board_id, name, position, wip_limit
- **cards**: card_id, list_id, board_id, title, description, due_date, labels, priority, assigned_members, attachments, checklist, comments
- **pending_invites**: invite_id, email, invite_type, target_id, board_id, invited_by
- **invitation_tokens**: token, email, invitation_type, target_id, role, invited_by, target_name, used, expires_at
- **email_logs**: log_id, to_email, subject, email_type, success, error, invitation_token, sent_at
- **notifications**: notification_id, user_id, type, title, message, read

## Test Credentials
- **Admin**: odapto.admin@emergent.com / SecurePassword123!
- **Test Board**: board_8b24ee8c579c
- **Test Workspace**: ws_3a39c12c673e

## Environment Variables (Backend)
- MONGO_URL - MongoDB connection string
- DB_NAME - Database name
- CORS_ORIGINS - Allowed CORS origins
- SMTP_HOST - Gmail SMTP host (smtp.gmail.com)
- SMTP_PORT - SMTP port (587)
- SMTP_USERNAME - Gmail address
- SMTP_PASSWORD - Gmail App Password
- SMTP_FROM_NAME - Email sender name (Odapto)
- FRONTEND_URL - Frontend base URL for invitation links

## Next Tasks
1. Implement real-time board sync via WebSockets
2. Add card activity/history log
3. Add board filters (by label, due date, member)
4. Implement keyboard shortcuts
5. Add card cover images

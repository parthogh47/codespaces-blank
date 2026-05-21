# AI-Based Skill Partner Finder - PRD

## Original Problem Statement
AI-Based Skill Partner Finder app with modern, friendly theme. Users upload profile picture, enter skills with proficiency levels, and get AI-powered matchmaking with potential learning partners. Features include conversation starters, mini-challenges, achievements, and social sharing.

**Theme**: Modern, friendly, motivational with Indigo (#4F46E5), Emerald (#10B981), Amber (#FBBF24), Light Gray (#F3F4F6), Dark Gray (#111827).

## Architecture
- **Backend**: FastAPI + MongoDB
- **Frontend**: React 19 + Tailwind CSS + Shadcn UI
- **AI**: OpenAI GPT-4o via emergentintegrations + Emergent LLM Key
- **Storage**: Emergent Object Storage for profile pictures
- **Auth**: JWT with httpOnly cookies (Secure + SameSite=none)

## User Personas
1. **Learner**: Wants to find a partner to learn complementary skills
2. **Mentor/Mentee**: Wants to teach/learn from someone with complementary expertise
3. **Collaborator**: Looking for project partners with diverse skills

## Core Requirements (Static)
- User registration/login with JWT auth
- Onboarding with profile picture upload + skills input
- AI-powered skill matchmaking (3-5 matches per user)
- Match details with conversation starters (copy-to-clipboard)
- Mini-challenges and achievements system
- Social sharing hooks

## What's Been Implemented (Feb 2026)
- Full JWT auth flow (register, login, logout, refresh, /me)
- Profile management endpoints
- Profile picture upload via Emergent Object Storage with auth-protected downloads
- AI matchmaking via OpenAI GPT-4o with markdown-fence sanitization
- Dashboard with matches, challenges, achievements
- Match details page with copy-to-clipboard conversation starters
- Brute force protection on login
- Admin seeding on startup
- Full design system per design_guidelines.json

## Feature Expansion #2 (Feb 2026)
- **Profile Edit Page** (/profile): Edit name, bio, skills, proficiency, profile picture
- **Real User Matching** (/api/matches/real): Find actual users in DB with overlapping/complementary skills, shown as green-bordered cards on Dashboard
- **Messaging System** (/messages, /messages/:id): Full conversations with persistent messages; "Start Collaboration" button on real-user matches creates conversation and navigates to chat
- **Share Match Feature** (/share/:token): Generate public shareable link for an AI match (viewable without login) - perfect viral hook for user acquisition
- **Achievement Auto-Award**: Sending first message awards "Collaborator" achievement
- **Indexes added**: conversations.participants, messages (conversation_id+created_at), shared_matches.token
- **Tests**: 35/35 backend tests pass; frontend E2E verified end-to-end

## Tech Decisions
- Used Emergent LLM Key for OpenAI GPT-4o (no separate billing)
- Used Emergent Object Storage (no S3 setup needed)
- Cookies set with `Secure=True, SameSite=none` for HTTPS preview
- Match results cached in MongoDB per user (regenerate via refresh button)

## Prioritized Backlog
### P0 (None - core is complete)

### P1 (Future)
- Real partner matching (currently AI generates fictional profiles - could connect real users)
- Direct messaging between matched users
- Profile editing screen (currently only via onboarding)
- Leaderboard for completed challenges

### P2 (Nice-to-have)
- Email notifications for new matches
- Skill endorsements from peers
- Video calling for collaborations
- Match rating/feedback system
- LinkedIn import for skills

## Next Tasks
- Add a profile edit page (currently users can only edit during onboarding)
- Wire up "Start Collaboration" button to actual messaging
- Connect AI matches to real users in the database for actual social networking

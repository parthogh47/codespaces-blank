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
- 15/15 backend tests passing, frontend E2E verified

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

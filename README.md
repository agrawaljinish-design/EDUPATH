# EduPath — Personalized Learning & Skill Gap Agent

> **An Autonomous Adaptive AI Learning Engine with Continuous Diagnosis, Dynamic Path Replanning, Real-time Peer Collaboration, and Gamified Motivation.**

---

## 1. Product Overview

Static course roadmaps fail because every learner arrives with distinct foundational knowledge, learning velocities, and stumbling blocks. **EduPath** replaces rigid course tracks with an autonomous, adaptive AI learning loop:

```text
Learner Profile
      ↓
Resume / Portfolio Analysis (PyMuPDF)
      ↓
Skill Extraction & Verification
      ↓
Target Role Gap Diagnosis
      ↓
Diagnostic Assessment
      ↓
Personalized Roadmap Synthesis (Topological Dependency Ordering)
      ↓
Daily & Weekly Study Plan
      ↓
Learn & Practice
      ↓
Continuous Struggle Detection ("I'm Stuck" / Low Checkpoint Scores)
      ↓
Adaptive Replanning (Revision + Targeted Practice Checkpoints Inserted)
      ↓
Updated Active Roadmap
```

### The Three Core Product Pillars
1. **Personalized Learning**: Dynamic skill extraction, target role skill mapping (11+ canonical roles + arbitrary roles), topological dependency sequencing, daily/weekly micro-plans, hands-on portfolio projects, spaced repetition (SM-2 intervals), and automatic struggle intervention.
2. **Peer Collaboration**: Real learner-to-learner interaction (no simulated AI peer answers). Complementary skill matching, bidirectional friend requests, doubt forum with helpful votes and author-only best answer designation, study groups, and community discussions.
3. **Competitive Gamification**: Immutable event-sourced XP ledger (`xp_events`), daily study streaks, multi-tier leaderboards (Global, Weekly, Monthly, Friends), active challenges, and automatic milestone badges.

---

## 2. Architecture & Technology Stack

- **Frontend**: HTML5, Modern Vanilla CSS (Custom Properties, Glassmorphism, Responsive Grid, Animations), Vanilla JavaScript. **Zero heavy JavaScript frameworks** (no React, Vue, Angular, or TypeScript).
- **Backend**: Python 3.11+ / 3.14, FastAPI, Uvicorn, Pydantic, python-multipart.
- **AI Engine**: OpenAI API (`gpt-4o-mini` / `gpt-4o`) with structured JSON schema enforcement and robust deterministic fallback algorithms for offline resilience.
- **Database & Persistence**: Firebase Firestore via Firebase Admin SDK with automatic persistent local JSON fallback (`backend/data/local_db.json`) ensuring 100% offline uptime and zero data loss across restarts.
- **Resume & PDF Parsing**: PyMuPDF (`fitz`) for low-latency text and layout extraction from candidate PDFs.

---

## 3. Project Directory Structure

```text
EDUPATH/
├── frontend/
│   ├── index.html           # Modern landing page & Try Demo CTA
│   ├── login.html           # Real learner login & 1-click Demo mode launcher
│   ├── dashboard.html       # Primary learner hub (stats, today's plan, companion)
│   ├── profile.html         # Learner profile & target career configuration
│   ├── resume.html          # PyMuPDF PDF parser & extraction verification
│   ├── skills.html          # Visual skill gap matrix & confidence indicators
│   ├── roadmap.html         # Interactive adaptive roadmap timeline
│   ├── plan.html            # Daily & weekly study plan matching declared hours
│   ├── assessment.html      # Diagnostic assessment & instant scoring
│   ├── revision.html        # Spaced repetition queue & interactive flashcards
│   ├── projects.html        # Gap-closing practical portfolio project generator
│   ├── chat.html            # Context-aware AI Learning Companion
│   ├── peers.html           # Complementary peer discovery & matching
│   ├── friends.html         # Mutual friends and pending request management
│   ├── doubts.html          # Doubt resolution forum (helpful upvotes & best answer)
│   ├── groups.html          # Collaborative student study circles
│   ├── community.html       # Community posts, achievements, and discussions
│   ├── challenges.html      # Gamified learning challenges & XP rewards
│   ├── leaderboard.html     # Global, weekly, monthly, and friends leaderboards
│   ├── badges.html          # Milestone achievement badges & unlock criteria
│   ├── progress.html        # Verified activity logs & consistency analytics
│   ├── reports.html         # Weekly AI performance narrative & strategic focus
│   ├── style.css            # Unified modern CSS design system
│   └── script.js            # Central API client, session management, and struggle modal
├── backend/
│   ├── main.py              # FastAPI application, static mounting & 30+ REST endpoints
│   ├── requirements.txt     # Backend dependency specification
│   ├── .env.example         # Environment template without secrets
│   ├── .env                 # Local configuration
│   ├── agent/
│   │   ├── agent.py         # EduPath Orchestrator & Demo seeder
│   │   └── prompts.py       # Prompt templates for Companion & Weekly Reports
│   ├── tools/
│   │   ├── resume_parser.py # PyMuPDF PDF text extraction
│   │   ├── skill_analyzer.py# Deterministic gap & canonical role engine
│   │   ├── assessment.py    # Diagnostic question generator & evaluator
│   │   ├── resource_search.py# Curated educational resource recommender
│   │   ├── planner.py       # Personalized topological roadmap & daily planner
│   │   ├── progress_tracker.py# Event-based XP ledger, streaks & badges
│   │   ├── struggle_detector.py# Multi-signal struggle detection & replanning
│   │   ├── revision.py      # Spaced repetition engine (SM-2 intervals)
│   │   ├── project_generator.py# Gap-closing project architect
│   │   ├── peer_engine.py   # Peer matching, friends, doubts & permissions
│   │   └── competition_engine.py# Leaderboards, challenges & tournament attempts
│   ├── services/
│   │   ├── firebase.py      # Firestore abstraction with persistent local fallback
│   │   └── openai_service.py# OpenAI client with offline fallback
│   └── models/
│       └── schemas.py       # Pydantic data contracts
├── .gitignore               # Strict exclusion of secrets, venv, and caches
└── README.md                # Complete documentation and quickstart guide
```

---

## 4. Setup & Running Locally

### Step 1: Clone Repository & Enter Directory
```bash
git clone <your-repo-url>
cd EDUPATH
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `backend/.env`:
```bash
cp backend/.env.example backend/.env
```
Edit `backend/.env` with your API keys (optional — EduPath runs fully with intelligent deterministic fallbacks if keys are not set):
```ini
OPENAI_API_KEY=your_openai_key_here
FIREBASE_CREDENTIALS_PATH=
FIREBASE_PROJECT_ID=
HOST=127.0.0.1
PORT=8000
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Start Backend Server
```bash
cd backend
python3 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Step 5: Access Frontend
Open your browser and navigate to:
```text
http://127.0.0.1:8000/
```
The FastAPI backend automatically serves all frontend HTML, CSS, and JS files directly.

---

## 5. Dual Operation Modes: Real Learner vs Demo Mode

### Real Learner Mode
- Every user gets a unique `user_id` (e.g. `user_sarah`, `user_alexa`).
- Background skills, target role, and career goals originate exclusively from their profile, uploaded PDF resume, or assessment submissions.
- Roadmaps and gap matrices are synthesized dynamically from their personal deficits.
- Changing target role (e.g. from `AI/ML Engineer` to `Frontend Developer`) immediately recalculates gaps and restructures roadmap milestones.

### Demo Mode (Alex Demo)
- Pre-seeded specifically for hackathon evaluation:
  - **Learner**: Alex Demo (`demo_learner`)
  - **Target Role**: AI/ML Engineer
  - **Initial Skills**: Python, C++, HTML, MySQL basics
  - **Initial Roadmap**: NumPy → Pandas → Machine Learning → Statistics
  - **The Iconic Adaptive Struggle Story**:
    1. Learner struggles with SQL JOINs or clicks **I'm Stuck**.
    2. EduPath detects the struggle signal.
    3. The adaptive engine explains the bottleneck, creates a revision card deck, schedules an easier micro-practice task, and **automatically restructures the roadmap** by inserting an adaptive reinforcement checkpoint before downstream milestones.

---

## 6. Comprehensive REST API Endpoints

| Category | Endpoint | Method | Purpose |
| :--- | :--- | :--- | :--- |
| **System** | `/health` | `GET` | Reports status of OpenAI, Firebase, and collections |
| **Profile** | `/profile` | `POST` | Create or update learner profile |
| **Profile** | `/profile/{user_id}` | `GET` | Retrieve learner profile |
| **Profile** | `/resume/upload` | `POST` | Extract structured entities from PDF via PyMuPDF |
| **Profile** | `/profile/analyze` | `POST` | Confirm extracted resume data & calculate initial gaps |
| **Skills** | `/skill-gaps/analyze` | `POST` | Calculate deterministic skill gaps & priorities |
| **Skills** | `/skills/{user_id}` | `GET` | List verified skill confidences & gap records |
| **Assessment** | `/assessment/generate`| `POST` | Generate 5 diagnostic questions (no client answers) |
| **Assessment** | `/assessment/evaluate`| `POST` | Grade submission, update confidence & detect struggle |
| **Roadmap** | `/roadmap/generate` | `POST` | Synthesize topological dependency roadmap |
| **Roadmap** | `/roadmap/{user_id}` | `GET` | Retrieve active roadmap with 'Why Learn This' |
| **Roadmap** | `/roadmap/replan` | `POST` | Trigger adaptive path replanning |
| **Plan** | `/plan/generate` | `POST` | Generate daily task list & weekly hour schedule |
| **Plan** | `/plan/today` | `GET` | Get today's focused learning activities |
| **Progress** | `/activity/complete` | `POST` | Complete activity, award XP & update streak |
| **Progress** | `/progress/{user_id}` | `GET` | Full analytics summary, hours, & streak history |
| **Struggle** | `/struggle/detect` | `POST` | "I'm Stuck" trigger, diagnosis & adaptive replan |
| **Revision** | `/revision/{user_id}` | `GET` | Get due spaced repetition flashcards |
| **Revision** | `/revision/generate` | `POST` | Add custom topic to spaced repetition queue |
| **Revision** | `/revision/review` | `POST` | Record flashcard score & compute SM-2 interval |
| **Projects** | `/project/generate` | `POST` | Architect personalized gap-closing portfolio project |
| **Chat** | `/chat` | `POST` | Context-aware AI companion conversational tutor |
| **Chat** | `/chat/{user_id}` | `GET` | Retrieve chat message history |
| **Reports** | `/reports/weekly/{id}`| `GET` | Synthesize executive weekly performance report |
| **Peers** | `/peers` | `GET` | Complementary peer recommendations |
| **Peers** | `/friends/request` | `POST` | Send bidirectional friend request |
| **Peers** | `/friends/accept` | `POST` | Accept friend request & create mutual friendship |
| **Peers** | `/friends/{user_id}` | `GET` | List mutual friends & incoming requests |
| **Doubts** | `/doubts` | `GET`, `POST` | Browse doubt forum & post technical question |
| **Doubts** | `/doubts/{id}/answers`| `POST` | Submit peer answer to a question |
| **Doubts** | `/answers/{id}/helpful`| `POST` | Upvote answer (+15 XP, +5 reputation to author) |
| **Doubts** | `/answers/{id}/best` | `POST` | Mark Best Answer (Author only, +50 XP, +20 rep) |
| **Groups** | `/groups` | `GET`, `POST` | List and create study circles |
| **Groups** | `/groups/{id}/join` | `POST` | Join collaborative study group |
| **Groups** | `/groups/{id}/leave` | `POST` | Leave study group |
| **Community** | `/community/posts` | `GET`, `POST` | View community feed & publish achievements/projects |
| **Competition**| `/leaderboard` | `GET` | Global, Weekly, Monthly leaderboard rankings |
| **Competition**| `/leaderboard/friends/{id}`| `GET` | Friends-only leaderboard |
| **Competition**| `/challenges` | `GET` | List challenges with user progress status |
| **Competition**| `/challenges/{id}/join`| `POST` | Enroll in challenge |
| **Competition**| `/challenges/{id}/complete`| `POST` | Complete challenge & award rewards |
| **Competition**| `/badges/{user_id}` | `GET` | List earned and locked milestone badges |
| **Demo** | `/demo/load` | `POST` | Seed isolated Alex Demo struggle scenario |

---

## 7. Database Collections Structure

EduPath organizes records across 26 Firestore / persistent collections:

```text
users                 # User accounts and credentials
profiles              # Comprehensive learner profiles
skills                # Verified skill confidence levels & history
skill_gaps            # Calculated deficits against target roles
roadmaps              # Topological learning path milestones
learning_objectives   # Granular progress objectives
resources             # Curated documentation and tutorials
activities            # Logged activity completion records
assessments           # Generated diagnostic tests (with server answers)
assessment_results    # Submissions, scores, feedback & weak areas
revision_queue        # Spaced repetition flashcards & SM-2 intervals
projects              # Personalized portfolio capstones
progress              # Aggregated XP, streak, hours, and reputation
reports               # Generated weekly AI performance reports
plans                 # Daily micro-plans & weekly schedules
chat_history          # Persistent context conversation log
friend_requests       # Bidirectional friend invitations
friends               # Mutual peer connections
groups                # Collaborative study groups
group_members         # Group roster
community_posts       # Community feed discussions & milestones
community_comments    # Threaded responses
doubts                # Peer doubt forum questions
answers               # Peer answers with helpful & best flags
xp_events             # Event-sourced immutable XP ledger
leaderboards          # Aggregated rank caches
challenges            # System challenges
user_challenges       # Learner enrollment and completion states
badges                # Badge definitions
user_badges           # Unlocked learner achievements
competitions          # Active tournament speedruns
competition_attempts  # Tournament scoring attempts
```

---

## 8. Verification & Test Suite

Run the end-to-end test suite verifying all tools, real learner vs demo separation, PyMuPDF parsing, struggle adaptation, and peer/competitive flows:

```bash
python3 test_edupath.py
```

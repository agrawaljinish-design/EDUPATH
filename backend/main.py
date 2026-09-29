import os
import sys
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from services.firebase import db_service
from services.openai_service import openai_service
from models.schemas import (
    LearnerProfile, ExtractedResumeData, SkillGap, AssessmentSubmission,
    ActivityCompletionRequest
)
from tools.resume_parser import resume_parser
from tools.skill_analyzer import skill_analyzer
from tools.assessment import assessment_engine
from tools.planner import planner
from tools.progress_tracker import progress_tracker
from tools.struggle_detector import struggle_detector
from tools.revision import revision_engine
from tools.project_generator import project_generator
from tools.peer_engine import peer_engine
from tools.competition_engine import competition_engine
from agent.agent import edupath_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edupath.main")

app = FastAPI(
    title="EduPath API — Personalized Learning & Skill Gap Agent",
    description="Adaptive AI learning engine: skill gaps, dynamic roadmaps, struggle detection, peer collaboration, and gamification.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# --- System Health ---
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "openai": openai_service.check_health(),
        "firebase": db_service.is_connected,
        "firebase_mode": db_service.mode,
        "database_collections": db_service.get_collection_counts()
    }

# --- Profile Endpoints ---
@app.post("/profile")
def save_profile(profile: LearnerProfile):
    doc = db_service.save("profiles", profile.user_id, profile.model_dump())
    # Ensure progress record exists
    progress_tracker.get_user_progress(profile.user_id)
    return {"status": "success", "profile": doc}

@app.get("/profile/{user_id}")
def get_profile(user_id: str):
    doc = db_service.get("profiles", user_id)
    if not doc:
        # If user_id == demo_learner, seed it automatically
        if user_id == "demo_learner":
            edupath_agent.seed_demo_learner()
            doc = db_service.get("profiles", user_id)
        else:
            default_p = LearnerProfile(user_id=user_id, name=f"User {user_id[:6]}")
            doc = db_service.save("profiles", user_id, default_p.model_dump())
    return doc

@app.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
    try:
        content = await file.read()
        extracted = resume_parser.parse_resume(content)
        return {"status": "success", "data": extracted.model_dump()}
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

class ProfileAnalyzeRequest(BaseModel):
    user_id: str
    target_role: str
    current_skills: List[str]
    education: Optional[str] = "Undergraduate Degree"
    experience: Optional[str] = "Student"
    hours_per_week: Optional[int] = 10

@app.post("/profile/analyze")
def analyze_and_update_profile(req: ProfileAnalyzeRequest):
    existing = db_service.get("profiles", req.user_id) or {}
    existing.update({
        "user_id": req.user_id,
        "target_role": req.target_role,
        "current_skills": req.current_skills,
        "education": req.education or existing.get("education", "Undergraduate Degree"),
        "experience": req.experience or existing.get("experience", "Student"),
        "hours_per_week": req.hours_per_week or existing.get("hours_per_week", 10)
    })
    saved = db_service.save("profiles", req.user_id, existing)
    
    # Analyze initial gaps
    gaps = skill_analyzer.analyze_gaps(req.current_skills, [], req.target_role)
    return {"status": "success", "profile": saved, "gaps": [g.model_dump() for g in gaps]}

# --- Skill & Gap Endpoints ---
class SkillGapAnalyzeRequest(BaseModel):
    user_id: str
    target_role: Optional[str] = None

@app.post("/skill-gaps/analyze")
def analyze_skill_gaps(req: SkillGapAnalyzeRequest):
    profile_doc = db_service.get("profiles", req.user_id)
    if not profile_doc:
        raise HTTPException(status_code=404, detail="Profile not found.")

    target_role = req.target_role or profile_doc.get("target_role", "Software Engineer")
    current_skills = profile_doc.get("current_skills", [])
    
    # User skill records
    skill_items = db_service.query("skills", filters=[("user_id", "==", req.user_id)])
    skill_item_objs = []
    for item in skill_items:
        from models.schemas import SkillItem
        skill_item_objs.append(SkillItem(**item))

    gaps = skill_analyzer.analyze_gaps(current_skills, skill_item_objs, target_role)

    # Save gaps
    for g in gaps:
        gap_id = f"{req.user_id}_{g.skill.lower().replace(' ', '_')}"
        gap_doc = g.model_dump()
        gap_doc["user_id"] = req.user_id
        db_service.save("skill_gaps", gap_id, gap_doc)

    return {"status": "success", "target_role": target_role, "gaps": [g.model_dump() for g in gaps]}

@app.get("/skills/{user_id}")
def get_user_skills(user_id: str):
    skills = db_service.query("skills", filters=[("user_id", "==", user_id)])
    gaps = db_service.query("skill_gaps", filters=[("user_id", "==", user_id)])
    return {"skills": skills, "gaps": gaps}

# --- Assessment Endpoints ---
class AssessmentGenerateRequest(BaseModel):
    user_id: str
    skill: str
    difficulty: Optional[str] = "Medium"

@app.post("/assessment/generate")
def generate_assessment(req: AssessmentGenerateRequest):
    assessment = assessment_engine.generate_assessment(req.user_id, req.skill, req.difficulty or "Medium")
    # Clean output for frontend (no answers exposed)
    clean_data = assessment_engine.get_clean_assessment_for_client(assessment)
    return clean_data

@app.post("/assessment/evaluate")
def evaluate_assessment(submission: AssessmentSubmission):
    try:
        result = assessment_engine.evaluate_submission(submission)
        # Award XP for assessment completion
        progress_tracker.award_xp(submission.user_id, 50, "assessment", f"Completed {result.skill} assessment ({result.score}%)")
        # Check First Assessment Badge
        progress_tracker.award_badge_if_not_held(submission.user_id, "badge_first_assessment")
        
        # If score is very low, trigger struggle detection automatically
        if result.score < 50:
            struggle_detector.detect_and_intervene(
                user_id=submission.user_id,
                skill=result.skill,
                topic="Assessment fundamentals",
                trigger_type="low_score",
                details=f"Scored {result.score}% in diagnostic assessment"
            )

        return result.model_dump()
    except Exception as e:
        logger.error(f"Assessment evaluate error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# --- Roadmap Endpoints ---
class RoadmapGenerateRequest(BaseModel):
    user_id: str

@app.post("/roadmap/generate")
def generate_roadmap(req: RoadmapGenerateRequest):
    profile_doc = db_service.get("profiles", req.user_id)
    if not profile_doc:
        raise HTTPException(status_code=404, detail="Profile not found.")
    profile = LearnerProfile(**profile_doc)

    # Analyze gaps
    user_skills = db_service.query("skills", filters=[("user_id", "==", req.user_id)])
    gaps = skill_analyzer.analyze_gaps(profile.current_skills, [], profile.target_role)

    roadmap = planner.generate_roadmap(req.user_id, profile, gaps)
    # Also generate today's plan
    planner.generate_daily_plan(req.user_id, roadmap, profile.hours_per_week)
    return roadmap.model_dump()

@app.get("/roadmap/{user_id}")
def get_roadmap(user_id: str):
    doc = db_service.get_latest("roadmaps", user_id)
    if not doc:
        # Generate automatically
        p_doc = db_service.get("profiles", user_id)
        if p_doc:
            return generate_roadmap(RoadmapGenerateRequest(user_id=user_id))
        raise HTTPException(status_code=404, detail="No roadmap found for user.")
    return doc

class ReplanRequest(BaseModel):
    user_id: str
    skill: str
    topic: Optional[str] = ""
    reason: Optional[str] = "Manual replan request"

@app.post("/roadmap/replan")
def replan_roadmap(req: ReplanRequest):
    struggle_event = struggle_detector.detect_and_intervene(
        user_id=req.user_id,
        skill=req.skill,
        topic=req.topic or "Topic revision",
        trigger_type="manual_replan",
        details=req.reason or "Requested adaptive path update"
    )
    latest_roadmap = db_service.get_latest("roadmaps", req.user_id)
    return {
        "status": "success",
        "struggle_event": struggle_event.model_dump(),
        "updated_roadmap": latest_roadmap
    }

# --- Plan Endpoints ---
class PlanGenerateRequest(BaseModel):
    user_id: str

@app.post("/plan/generate")
def generate_plan(req: PlanGenerateRequest):
    roadmap_doc = db_service.get_latest("roadmaps", req.user_id)
    if not roadmap_doc:
        raise HTTPException(status_code=400, detail="Please generate a roadmap first.")
    from models.schemas import Roadmap
    roadmap = Roadmap(**roadmap_doc)
    profile_doc = db_service.get("profiles", req.user_id) or {}
    hours = profile_doc.get("hours_per_week", 10)

    daily = planner.generate_daily_plan(req.user_id, roadmap, hours)
    weekly = planner.generate_weekly_plan(req.user_id, roadmap, hours)
    return {"daily_plan": daily.model_dump(), "weekly_plan": weekly.model_dump()}

@app.get("/plan/today")
def get_today_plan(user_id: str = Query(...)):
    doc = db_service.get_latest("plans", user_id)
    if not doc:
        roadmap_doc = db_service.get_latest("roadmaps", user_id)
        if roadmap_doc:
            from models.schemas import Roadmap
            roadmap = Roadmap(**roadmap_doc)
            return planner.generate_daily_plan(user_id, roadmap).model_dump()
        return {"today_objective": "Start by generating your personalized roadmap!", "learning_activities": [], "practice_tasks": [], "revision_tasks": []}
    return doc

# --- Activity & Progress Endpoints ---
@app.post("/activity/complete")
def complete_activity(req: ActivityCompletionRequest):
    result = progress_tracker.complete_activity(req)
    return result

@app.get("/progress/{user_id}")
def get_progress(user_id: str):
    summary = progress_tracker.get_user_progress(user_id)
    activities = db_service.query("activities", filters=[("user_id", "==", user_id)], limit=10)
    user_badges = db_service.query("user_badges", filters=[("user_id", "==", user_id)])
    assessment_results = db_service.query("assessment_results", filters=[("user_id", "==", user_id)])
    assessments_passed = len([r for r in assessment_results if int(r.get("score", 0) or 0) >= 60])
    summary_data = summary.model_dump()
    summary_data["assessments_passed"] = assessments_passed
    return {
        "summary": summary_data,
        "recent_activities": activities,
        "badges": user_badges
    }

# --- Struggle & "I'm Stuck" Endpoint ---
class StruggleRequest(BaseModel):
    user_id: str
    skill: str
    topic: Optional[str] = ""
    details: Optional[str] = ""

@app.post("/struggle/detect")
def trigger_struggle_intervention(req: StruggleRequest):
    event = struggle_detector.detect_and_intervene(
        user_id=req.user_id,
        skill=req.skill,
        topic=req.topic or "Foundational syntax and logic",
        trigger_type="im_stuck_button",
        details=req.details or "Student pressed I'm Stuck"
    )
    latest_roadmap = db_service.get_latest("roadmaps", req.user_id)
    return {
        "status": "struggle_resolved",
        "event": event.model_dump(),
        "updated_roadmap": latest_roadmap
    }

# --- Revision Endpoints ---
@app.get("/revision/{user_id}")
def get_revision_queue(user_id: str):
    items = revision_engine.get_due_revisions(user_id)
    return {"revisions": items}

class RevisionGenerateRequest(BaseModel):
    user_id: str
    skill: str
    topic: str

@app.post("/revision/generate")
def generate_revision(req: RevisionGenerateRequest):
    item = revision_engine.add_to_queue(req.user_id, req.skill, req.topic)
    return item

class RevisionReviewRequest(BaseModel):
    user_id: str
    item_id: str
    score: int

@app.post("/revision/review")
def record_revision_review(req: RevisionReviewRequest):
    updated = revision_engine.record_review(req.user_id, req.item_id, req.score)
    # Award XP
    progress_tracker.award_xp(req.user_id, 20, "revision", f"Completed flashcard review ({req.score}%)")
    return updated

# --- Projects Endpoints ---
class ProjectGenerateRequest(BaseModel):
    user_id: str

@app.post("/project/generate")
def generate_project(req: ProjectGenerateRequest):
    profile_doc = db_service.get("profiles", req.user_id)
    if not profile_doc:
        raise HTTPException(status_code=404, detail="Profile not found.")
    profile = LearnerProfile(**profile_doc)
    gaps = skill_analyzer.analyze_gaps(profile.current_skills, [], profile.target_role)
    project = project_generator.generate_project(req.user_id, profile, gaps)
    return project.model_dump()

@app.get("/projects/{user_id}")
def list_user_projects(user_id: str):
    projects = db_service.query("projects", filters=[("user_id", "==", user_id)])
    return {"projects": projects}

# --- Chat AI Companion Endpoints ---
class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
def chat_with_companion(req: ChatRequest):
    reply = edupath_agent.handle_chat(req.user_id, req.message)
    return {"response": reply}

@app.get("/chat/{user_id}")
def get_chat_history(user_id: str):
    history = db_service.query("chat_history", filters=[("user_id", "==", user_id)], order_by="timestamp", descending=False, limit=30)
    return {"history": history}

# --- Reports Endpoint ---
@app.get("/reports/weekly/{user_id}")
def get_weekly_report(user_id: str):
    report = edupath_agent.generate_weekly_report(user_id)
    return report.model_dump()

# --- Peer System Endpoints ---
@app.get("/peers")
def get_peers(user_id: str = Query(...)):
    return {"peers": peer_engine.get_peer_recommendations(user_id)}

class FriendReqBody(BaseModel):
    from_user_id: str
    to_user_id: str

@app.post("/friends/request")
def send_friend_request(body: FriendReqBody):
    return peer_engine.send_friend_request(body.from_user_id, body.to_user_id)

class FriendAcceptBody(BaseModel):
    request_id: str
    user_id: str

@app.post("/friends/accept")
def accept_friend_request(body: FriendAcceptBody):
    return peer_engine.accept_friend_request(body.request_id, body.user_id)

@app.get("/friends/{user_id}")
def list_friends(user_id: str):
    friends = peer_engine.list_friends(user_id)
    pending = peer_engine.list_pending_requests(user_id)
    return {"friends": friends, "pending_requests": pending}

class CreateDoubtBody(BaseModel):
    user_id: str
    title: str
    description: str
    skill: str
    difficulty: Optional[str] = "Medium"
    topic: Optional[str] = None

@app.post("/doubts")
def create_doubt(body: CreateDoubtBody):
    return peer_engine.create_doubt(body.user_id, body.title, body.description, body.skill, body.difficulty or "Medium")

@app.get("/doubts")
def list_doubts(skill: Optional[str] = None):
    return {"doubts": peer_engine.list_doubts(skill)}

class AnswerDoubtBody(BaseModel):
    user_id: str
    content: str

@app.post("/doubts/{doubt_id}/answers")
def answer_doubt(doubt_id: str, body: AnswerDoubtBody):
    return peer_engine.answer_doubt(doubt_id, body.user_id, body.content)

@app.get("/doubts/{doubt_id}/answers")
def get_doubt_answers(doubt_id: str):
    return {"answers": peer_engine.list_answers_for_doubt(doubt_id)}

class HelpfulBody(BaseModel):
    user_id: str

@app.post("/answers/{answer_id}/helpful")
def vote_helpful(answer_id: str, body: HelpfulBody):
    return peer_engine.vote_helpful(answer_id, body.user_id)

class BestAnswerBody(BaseModel):
    user_id: str
    doubt_id: str

@app.post("/answers/{answer_id}/best")
def mark_best_answer(answer_id: str, body: BestAnswerBody):
    try:
        return peer_engine.mark_best_answer(body.doubt_id, answer_id, body.user_id)
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class CreateGroupBody(BaseModel):
    user_id: str
    name: str
    description: str
    skills: List[str]
    target_role: Optional[str] = "All Roles"

@app.post("/groups")
def create_group(body: CreateGroupBody):
    return peer_engine.create_group(body.user_id, body.name, body.description, body.skills, body.target_role or "All Roles")

@app.get("/groups")
def list_groups():
    return {"groups": peer_engine.list_groups()}

@app.post("/groups/{group_id}/join")
def join_group(group_id: str, body: HelpfulBody):
    return peer_engine.join_group(group_id, body.user_id)

@app.post("/groups/{group_id}/leave")
def leave_group(group_id: str, body: HelpfulBody):
    return peer_engine.leave_group(group_id, body.user_id)

class CreatePostBody(BaseModel):
    user_id: str
    category: str
    title: str
    content: str

@app.post("/community/posts")
def create_community_post(body: CreatePostBody):
    return peer_engine.create_post(body.user_id, body.category, body.title, body.content)

@app.get("/community/posts")
def list_community_posts(category: Optional[str] = None):
    return {"posts": peer_engine.list_posts(category)}

class CommentBody(BaseModel):
    user_id: str
    content: str

@app.post("/community/posts/{post_id}/comments")
def add_comment(post_id: str, body: CommentBody):
    return peer_engine.add_comment(post_id, body.user_id, body.content)

@app.get("/community/posts/{post_id}/comments")
def get_comments(post_id: str):
    return {"comments": peer_engine.list_comments_for_post(post_id)}

# --- Competition Endpoints ---
@app.get("/leaderboard")
def get_leaderboard(timeframe: str = "global"):
    entries = competition_engine.get_leaderboard(timeframe=timeframe)
    return {"timeframe": timeframe, "leaderboard": [e.model_dump() for e in entries]}

@app.get("/leaderboard/friends/{user_id}")
def get_friends_leaderboard(user_id: str):
    entries = competition_engine.get_friends_leaderboard(user_id)
    return {"leaderboard": [e.model_dump() for e in entries]}

@app.get("/challenges")
def list_challenges(user_id: str = Query(...)):
    return {"challenges": competition_engine.get_challenges(user_id)}

@app.post("/challenges/{challenge_id}/join")
def join_challenge(challenge_id: str, body: HelpfulBody):
    return competition_engine.join_challenge(body.user_id, challenge_id)

@app.post("/challenges/{challenge_id}/complete")
def complete_challenge(challenge_id: str, body: HelpfulBody):
    return competition_engine.complete_challenge(body.user_id, challenge_id)

@app.get("/badges/{user_id}")
def list_user_badges(user_id: str):
    return {"badges": competition_engine.get_badges(user_id)}

@app.get("/competitions")
def list_competitions():
    return {"competitions": competition_engine.get_competitions()}

class AttemptCompBody(BaseModel):
    user_id: str
    score: int
    time_taken_seconds: int

@app.post("/competitions/{competition_id}/attempt")
def attempt_competition(competition_id: str, body: AttemptCompBody):
    return competition_engine.attempt_competition(body.user_id, competition_id, body.score, body.time_taken_seconds)

# --- Demo Seeding Endpoint ---
@app.post("/demo/load")
def load_demo():
    result = edupath_agent.seed_demo_learner()
    return result

# --- Static Frontend Mounting ---
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/style.css")
    def serve_style():
        return FileResponse(os.path.join(FRONTEND_DIR, "style.css"))

    @app.get("/script.js")
    def serve_script():
        return FileResponse(os.path.join(FRONTEND_DIR, "script.js"))

    @app.get("/{file_name:path}")
    def serve_static_or_page(file_name: str):
        # Prevent accessing files outside FRONTEND_DIR
        safe_path = os.path.normpath(os.path.join(FRONTEND_DIR, file_name))
        if not safe_path.startswith(os.path.abspath(FRONTEND_DIR)):
            raise HTTPException(status_code=403, detail="Forbidden")
        if os.path.exists(safe_path) and os.path.isfile(safe_path):
            return FileResponse(safe_path)
        raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- Profile Models ---
class LearnerProfile(BaseModel):
    user_id: str
    name: str = "Learner"
    education: str = "Undergraduate Computer Science"
    current_skills: List[str] = Field(default_factory=list)
    experience: str = "Student / Beginner"
    target_role: str = "AI/ML Engineer"
    career_goal: str = "Land an industry role within 6 months"
    hours_per_week: int = 10
    learning_preferences: List[str] = Field(default_factory=lambda: ["Videos", "Hands-on projects", "Quizzes"])
    preferred_difficulty: str = "Intermediate"
    preferred_format: str = "Interactive"
    projects: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ExtractedResumeData(BaseModel):
    skills: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    raw_text: str = ""

# --- Skill & Gap Models ---
class SkillConfidenceHistory(BaseModel):
    score: int
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SkillItem(BaseModel):
    skill: str
    confidence: int = 0  # 0 to 100
    evidence: str = "Initial assessment"
    category: str = "Core"
    history: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SkillGap(BaseModel):
    skill: str
    importance: str = "High"  # Critical, High, Medium, Low
    current_confidence: int = 0
    required_level: int = 80
    gap_level: str = "High"  # Critical, High, Medium, Low
    priority: float = 8.5
    dependencies: List[str] = Field(default_factory=list)
    reason: str = ""

class TargetRoleSkillMap(BaseModel):
    role: str
    skills: List[Dict[str, Any]] = Field(default_factory=list)
    description: str = ""

# --- Assessment Models ---
class AssessmentQuestion(BaseModel):
    id: str
    type: str = "mcq"  # mcq, short_answer, code
    question: str
    options: Optional[List[str]] = None
    code_snippet: Optional[str] = None
    correct_answer: Optional[str] = None  # Never exposed to client before submit
    explanation: Optional[str] = None
    difficulty: str = "Medium"  # Easy, Medium, Hard
    skill: str

class Assessment(BaseModel):
    id: str
    user_id: str
    skill: str
    difficulty: str = "Medium"
    questions: List[AssessmentQuestion]
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AssessmentSubmission(BaseModel):
    assessment_id: str
    user_id: str
    answers: Dict[str, str]  # question_id -> user answer

class AssessmentResult(BaseModel):
    id: str
    assessment_id: str
    user_id: str
    skill: str
    score: int  # 0 to 100
    correct_count: int
    total_count: int
    previous_confidence: int
    updated_confidence: int
    feedback: str
    weak_areas: List[str] = Field(default_factory=list)
    recommended_next_step: str
    answers_detail: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# --- Roadmap & Planner Models ---
class LearningObjective(BaseModel):
    id: str
    title: str
    description: str = ""
    completed: bool = False

class LearningResource(BaseModel):
    title: str
    type: str  # Video, Article, Documentation, Practice, Project
    url: str
    why_recommended: str
    estimated_time: str
    difficulty: str

class RoadmapItem(BaseModel):
    id: str
    skill: str
    priority: str = "High"
    objective: str
    objectives_list: List[LearningObjective] = Field(default_factory=list)
    resources: List[LearningResource] = Field(default_factory=list)
    estimated_hours: int = 5
    status: str = "Not Started"  # Not Started, In Progress, Completed, Needs Revision
    difficulty: str = "Medium"
    dependencies: List[str] = Field(default_factory=list)
    why_learning: str = ""
    unlocked_skills: List[str] = Field(default_factory=list)
    is_adaptation: bool = False  # Marked if inserted by struggle replanning

class Roadmap(BaseModel):
    id: str
    user_id: str
    target_role: str
    items: List[RoadmapItem] = Field(default_factory=list)
    version: int = 1
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    replan_history: List[Dict[str, Any]] = Field(default_factory=list)

class DailyPlan(BaseModel):
    id: str
    user_id: str
    date: str
    today_objective: str
    learning_activities: List[Dict[str, Any]] = Field(default_factory=list)
    practice_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    revision_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_minutes: int = 60
    completed: bool = False

class WeeklyPlan(BaseModel):
    id: str
    user_id: str
    week_start: str
    allocated_hours: int
    days: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)

# --- Struggle & Adaptive Models ---
class StruggleEvent(BaseModel):
    id: str
    user_id: str
    skill: str
    topic: str
    trigger_type: str  # low_score, repeated_fails, im_stuck_button
    explanation: str
    prerequisite_skill: Optional[str] = None
    before_roadmap_summary: List[str] = Field(default_factory=list)
    after_roadmap_summary: List[str] = Field(default_factory=list)
    intervention_action: str
    easier_practice_task: str
    revision_task: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# --- Revision & Spaced Repetition Models ---
class RevisionItem(BaseModel):
    id: str
    user_id: str
    skill: str
    topic: str
    last_reviewed: Optional[str] = None
    next_review: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    performance: int = 0  # 0 to 100
    interval_days: int = 1
    repetition_count: int = 0
    due: bool = True
    flashcards: List[Dict[str, str]] = Field(default_factory=list)

# --- Project Generator Models ---
class ProjectIdea(BaseModel):
    id: str
    user_id: str
    title: str
    problem: str
    why_it_matters: str
    skills_learned: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    difficulty: str = "Medium"
    estimated_hours: int = 12
    status: str = "Not Started"  # Not Started, In Progress, Completed

# --- Chat & AI Companion Models ---
class ChatMessage(BaseModel):
    id: str
    user_id: str
    role: str  # user, assistant
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# --- Peer & Collaboration Models ---
class FriendRequest(BaseModel):
    id: str
    from_user_id: str
    from_name: str
    to_user_id: str
    status: str = "pending"  # pending, accepted, rejected
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Friend(BaseModel):
    id: str
    user_id: str
    friend_user_id: str
    friend_name: str
    friend_role: str
    friend_streak: int = 1
    friend_xp: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Doubt(BaseModel):
    id: str
    user_id: str
    author_name: str
    title: str
    description: str
    skill: str
    difficulty: str = "Medium"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    best_answer_id: Optional[str] = None
    answers_count: int = 0

class DoubtAnswer(BaseModel):
    id: str
    doubt_id: str
    user_id: str
    author_name: str
    content: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    helpful_votes: int = 0
    helpful_voted_by: List[str] = Field(default_factory=list)
    is_best: bool = False

class StudyGroup(BaseModel):
    id: str
    name: str
    description: str
    skills: List[str] = Field(default_factory=list)
    target_role: str = "All Roles"
    creator_id: str
    creator_name: str
    members: List[Dict[str, str]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class CommunityPost(BaseModel):
    id: str
    user_id: str
    author_name: str
    category: str = "Discussion"  # Question, Project, Achievement, Discussion, Resource
    title: str
    content: str
    likes: int = 0
    liked_by: List[str] = Field(default_factory=list)
    comments_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class CommunityComment(BaseModel):
    id: str
    post_id: str
    user_id: str
    author_name: str
    content: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# --- Competitive & Gamification Models ---
class XPEvent(BaseModel):
    id: str
    user_id: str
    source: str  # activity, assessment, doubt_answer, best_answer, streak, challenge
    xp_amount: int
    description: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Challenge(BaseModel):
    id: str
    title: str
    description: str
    category: str  # coding, learning, peer, streak
    target_metric: str  # activities, assessments, doubts_helped, streak_days
    target_value: int
    xp_reward: int
    badge_reward: Optional[str] = None

class UserChallenge(BaseModel):
    id: str
    user_id: str
    challenge_id: str
    title: str
    current_value: int = 0
    target_value: int = 1
    xp_reward: int = 50
    status: str = "Available"  # Available, Joined, In Progress, Completed
    joined_at: Optional[str] = None
    completed_at: Optional[str] = None

class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    category: str
    criteria: str

class UserBadge(BaseModel):
    id: str
    user_id: str
    badge_id: str
    name: str
    description: str
    icon: str
    awarded_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    display_name: str
    target_role: str
    xp: int
    streak: int
    badges_count: int = 0

class Competition(BaseModel):
    id: str
    title: str
    description: str
    skill: str
    questions_count: int = 5
    xp_reward: int = 100
    active_until: str

class CompetitionAttempt(BaseModel):
    id: str
    competition_id: str
    user_id: str
    score: int
    time_taken_seconds: int
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# --- Progress & Report Models ---
class ActivityCompletionRequest(BaseModel):
    user_id: str
    activity_id: str
    skill: str
    title: str
    activity_type: str = "lesson"  # lesson, practice, revision, project
    time_spent_minutes: int = 30

class ProgressSummary(BaseModel):
    user_id: str
    completed_activities: int = 0
    completed_objectives: int = 0
    overall_confidence: int = 0
    streak: int = 1
    longest_streak: int = 1
    total_xp: int = 0
    learning_hours: float = 0.0
    roadmap_progress_percent: int = 0
    weak_areas: List[str] = Field(default_factory=list)
    reputation: int = 0

class WeeklyReport(BaseModel):
    id: str
    user_id: str
    week_title: str
    skills_improved: List[Dict[str, Any]] = Field(default_factory=list)
    objectives_completed: int = 0
    activities_completed: int = 0
    average_assessment_score: int = 0
    time_spent_hours: float = 0.0
    weak_areas: List[str] = Field(default_factory=list)
    revision_due_count: int = 0
    projects_progress: str = "On track"
    peer_contributions: int = 0
    xp_earned: int = 0
    current_streak: int = 1
    next_week_focus: List[str] = Field(default_factory=list)
    ai_summary: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

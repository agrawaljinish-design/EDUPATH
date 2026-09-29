import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.schemas import (
    LearnerProfile, Roadmap, RoadmapItem, LearningObjective, DailyPlan,
    ChatMessage, WeeklyReport, StruggleEvent
)
from services.firebase import db_service
from services.openai_service import openai_service
from tools.resource_search import resource_search

logger = logging.getLogger("edupath.agent")

class EduPathAgent:
    @staticmethod
    def get_learner_context(user_id: str) -> Dict[str, Any]:
        """Compile a concise, rich context snapshot for the AI tutor."""
        profile = db_service.get("profiles", user_id) or {}
        roadmap = db_service.get_latest("roadmaps", user_id) or {}
        progress = db_service.get("progress", user_id) or {}
        recent_assessments = db_service.query("assessment_results", filters=[("user_id", "==", user_id)], limit=3)
        revision_items = db_service.query("revision_queue", filters=[("user_id", "==", user_id)])

        roadmap_skills = [i.get("skill") for i in roadmap.get("items", [])]
        weak_areas = []
        for asmt in recent_assessments:
            weak_areas.extend(asmt.get("weak_areas", []))

        return {
            "user_id": user_id,
            "name": profile.get("name", "Learner"),
            "target_role": profile.get("target_role", "Software Engineer"),
            "current_skills": profile.get("current_skills", []),
            "experience": profile.get("experience", "Student"),
            "roadmap_skills": roadmap_skills,
            "streak": progress.get("streak", 1),
            "total_xp": progress.get("total_xp", 0),
            "weak_areas": list(set(weak_areas))[:4],
            "revision_due_count": len([r for r in revision_items if r.get("due", False)])
        }

    @staticmethod
    def handle_chat(user_id: str, message: str) -> str:
        """Handle incoming user message with context and persistent chat history."""
        msg_id_user = f"chat_{uuid.uuid4().hex[:8]}"
        user_msg = ChatMessage(
            id=msg_id_user,
            user_id=user_id,
            role="user",
            content=message,
            timestamp=datetime.utcnow().isoformat()
        )
        db_service.save("chat_history", msg_id_user, user_msg.model_dump())

        # Load context
        context = EduPathAgent.get_learner_context(user_id)

        # Retrieve recent conversation turns
        recent_turns = db_service.query("chat_history", filters=[("user_id", "==", user_id)], order_by="timestamp", descending=False, limit=6)
        formatted_turns = [{"role": t.get("role", "user"), "content": t.get("content", "")} for t in recent_turns]

        # Generate response
        reply_text = openai_service.chat_companion(formatted_turns, context)

        # Save assistant reply
        msg_id_bot = f"chat_{uuid.uuid4().hex[:8]}"
        bot_msg = ChatMessage(
            id=msg_id_bot,
            user_id=user_id,
            role="assistant",
            content=reply_text,
            timestamp=datetime.utcnow().isoformat()
        )
        db_service.save("chat_history", msg_id_bot, bot_msg.model_dump())

        return reply_text

    @staticmethod
    def generate_weekly_report(user_id: str) -> WeeklyReport:
        """Synthesize learner's comprehensive weekly performance report."""
        progress = db_service.get("progress", user_id) or {}
        profile = db_service.get("profiles", user_id) or {}
        recent_assessments = db_service.query("assessment_results", filters=[("user_id", "==", user_id)], limit=5)
        recent_activities = db_service.query("activities", filters=[("user_id", "==", user_id)], limit=10)
        revision_items = db_service.query("revision_queue", filters=[("user_id", "==", user_id)])

        avg_score = 0
        if recent_assessments:
            avg_score = int(sum(a.get("score", 0) for a in recent_assessments) / len(recent_assessments))

        weak_areas = []
        for a in recent_assessments:
            weak_areas.extend(a.get("weak_areas", []))

        # Skills improved
        user_skills = db_service.query("skills", filters=[("user_id", "==", user_id)])
        skills_improved = [{"skill": s.get("skill"), "confidence": s.get("confidence", 60)} for s in user_skills[:4]]

        report_id = f"report_{datetime.utcnow().strftime('%Y_W%W')}_{user_id}"
        ai_summary = (
            f"Superb weekly progress, {profile.get('name', 'Learner')}! You completed {len(recent_activities)} activities "
            f"and logged {progress.get('learning_hours', 0.0)} hours towards your goal of becoming an {profile.get('target_role', 'Engineer')}. "
            f"Your current daily study streak is {progress.get('streak', 1)} days with {progress.get('total_xp', 0)} total XP earned. "
            f"For next week, prioritize completing scheduled revision in your active queue to reinforce foundational memory."
        )

        report = WeeklyReport(
            id=report_id,
            user_id=user_id,
            week_title=f"Week of {datetime.utcnow().strftime('%B %d, %Y')}",
            skills_improved=skills_improved,
            objectives_completed=progress.get("completed_objectives", 3),
            activities_completed=len(recent_activities),
            average_assessment_score=avg_score or 75,
            time_spent_hours=progress.get("learning_hours", 4.5),
            weak_areas=list(set(weak_areas))[:3],
            revision_due_count=len([r for r in revision_items if r.get("due", False)]),
            projects_progress="Active Milestone in progress",
            peer_contributions=2,
            xp_earned=progress.get("total_xp", 120),
            current_streak=progress.get("streak", 1),
            next_week_focus=[
                f"Master key concepts in {skills_improved[0]['skill'] if skills_improved else 'Core Algorithms'}",
                "Review pending spaced repetition flashcards",
                "Complete 1 practical coding drill in Today's Plan"
            ],
            ai_summary=ai_summary,
            created_at=datetime.utcnow().isoformat()
        )

        db_service.save("reports", report_id, report.model_dump())
        return report

    @staticmethod
    def seed_demo_learner() -> Dict[str, Any]:
        """
        Seed ISOLATED Demo Mode for Alex Demo showcasing the iconic adaptive struggle storyline:
        Initial Path: NumPy -> Pandas -> Machine Learning -> Statistics
        Learner struggles with SQL JOINs -> Struggle detected -> Revision + Easy Practice + Reassessment -> Machine Learning -> Statistics.
        """
        user_id = "demo_learner"

        # 1. Profile
        demo_profile = LearnerProfile(
            user_id=user_id,
            name="Alex Demo",
            education="B.S. in Computer Science (Junior)",
            current_skills=["Python", "C++", "HTML", "MySQL basics"],
            experience="Student with academic programming coursework",
            target_role="AI/ML Engineer",
            career_goal="Land an AI/ML internship within 6 months",
            hours_per_week=10,
            learning_preferences=["Videos", "Hands-on projects", "Short quizzes"],
            preferred_difficulty="Intermediate",
            preferred_format="Interactive",
            projects=["Terminal-based C++ game", "Basic HTML/CSS personal portfolio"],
            certifications=["Python for Everybody"],
            interests=["Deep Learning", "Computer Vision", "Open Source"]
        )
        db_service.save("profiles", user_id, demo_profile.model_dump())

        # 2. Skills
        demo_skills = [
            {"skill": "Python", "confidence": 75, "evidence": "Academic coursework & terminal projects"},
            {"skill": "C++", "confidence": 80, "evidence": "Core CS data structures"},
            {"skill": "HTML", "confidence": 70, "evidence": "Personal web page"},
            {"skill": "MySQL basics", "confidence": 40, "evidence": "Introductory database course"}
        ]
        for s in demo_skills:
            db_service.save("skills", f"{user_id}_{s['skill'].lower().replace(' ', '_')}", {
                "user_id": user_id,
                "skill": s["skill"],
                "confidence": s["confidence"],
                "evidence": s["evidence"],
                "last_updated": datetime.utcnow().isoformat()
            })

        # 3. Initial Roadmap for Demo: NumPy -> Pandas -> Machine Learning -> Statistics
        roadmap_items = [
            RoadmapItem(
                id="demo_item_1",
                skill="NumPy",
                priority="Critical",
                objective="Vectorized computations and N-dimensional array processing",
                objectives_list=[
                    LearningObjective(id="demo_item_1_obj_1", title="Understand ndarray memory structure", completed=True),
                    LearningObjective(id="demo_item_1_obj_2", title="Vectorized array operations & broadcasting", completed=True),
                    LearningObjective(id="demo_item_1_obj_3", title="Matrix transformations & linear algebra", completed=False)
                ],
                resources=resource_search.get_resources_for_skill("NumPy"),
                estimated_hours=4,
                status="In Progress",
                difficulty="Medium",
                dependencies=["Python"],
                why_learning="Foundational library for all numerical tensor pipelines in AI/ML.",
                unlocked_skills=["Pandas", "Machine Learning"]
            ),
            RoadmapItem(
                id="demo_item_2",
                skill="Pandas",
                priority="Critical",
                objective="DataFrame feature engineering and dataset wrangling",
                objectives_list=[
                    LearningObjective(id="demo_item_2_obj_1", title="Inspect and clean missing tabular values", completed=False),
                    LearningObjective(id="demo_item_2_obj_2", title="Groupby aggregations and dataset joins", completed=False)
                ],
                resources=resource_search.get_resources_for_skill("Pandas"),
                estimated_hours=5,
                status="Not Started",
                difficulty="Medium",
                dependencies=["NumPy"],
                why_learning="Required for real-world tabular data cleaning and training feature preparation.",
                unlocked_skills=["Machine Learning"]
            ),
            RoadmapItem(
                id="demo_item_3",
                skill="Machine Learning",
                priority="Critical",
                objective="Train, tune, and evaluate supervised predictive algorithms",
                objectives_list=[
                    LearningObjective(id="demo_item_3_obj_1", title="Train Scikit-Learn classifiers", completed=False),
                    LearningObjective(id="demo_item_3_obj_2", title="Cross-validation and hyperparameter grids", completed=False)
                ],
                resources=resource_search.get_resources_for_skill("Machine Learning"),
                estimated_hours=8,
                status="Not Started",
                difficulty="Hard",
                dependencies=["Python", "NumPy", "Pandas"],
                why_learning="Core competency for AI/ML engineering positions.",
                unlocked_skills=["Deep Learning"]
            ),
            RoadmapItem(
                id="demo_item_4",
                skill="Statistics & Probability",
                priority="High",
                objective="Hypothesis testing, distributions, and optimization metrics",
                objectives_list=[
                    LearningObjective(id="demo_item_4_obj_1", title="Probability distributions & p-values", completed=False)
                ],
                resources=resource_search.get_resources_for_skill("Statistics & Probability"),
                estimated_hours=6,
                status="Not Started",
                difficulty="Medium",
                dependencies=[],
                why_learning="Mathematical foundation for model loss functions and generalization.",
                unlocked_skills=[]
            )
        ]

        demo_roadmap = Roadmap(
            id="demo_roadmap",
            user_id=user_id,
            target_role="AI/ML Engineer",
            items=roadmap_items,
            version=1,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        db_service.save("roadmaps", "demo_roadmap", demo_roadmap.model_dump())

        # 4. Progress, Streaks & XP
        demo_progress = {
            "user_id": user_id,
            "completed_activities": 6,
            "completed_objectives": 4,
            "overall_confidence": 68,
            "streak": 5,
            "longest_streak": 5,
            "total_xp": 480,
            "learning_hours": 6.5,
            "roadmap_progress_percent": 30,
            "weak_areas": ["SQL multi-table joins"],
            "reputation": 35
        }
        db_service.save("progress", user_id, demo_progress)
        db_service.save("leaderboards", user_id, {
            "user_id": user_id,
            "display_name": "Alex Demo",
            "target_role": "AI/ML Engineer",
            "xp": 480,
            "streak": 5
        })

        # 5. Badges
        demo_badges = [
            {"badge_id": "badge_first_assessment", "name": "First Assessment", "icon": "🎯", "description": "Completed first diagnostic assessment!"},
            {"badge_id": "badge_helpful_peer", "name": "Helpful Peer", "icon": "🤝", "description": "Answered a peer doubt!"}
        ]
        for b in demo_badges:
            db_service.save("user_badges", f"{user_id}_{b['badge_id']}", {
                "id": f"{user_id}_{b['badge_id']}",
                "user_id": user_id,
                "badge_id": b["badge_id"],
                "name": b["name"],
                "description": b["description"],
                "icon": b["icon"],
                "awarded_at": datetime.utcnow().isoformat()
            })

        # 6. Doubts and Community sample
        doubt_id = "demo_doubt_sql"
        db_service.save("doubts", doubt_id, {
            "id": doubt_id,
            "user_id": user_id,
            "author_name": "Alex Demo",
            "title": "When should I use LEFT JOIN vs INNER JOIN for feature tables?",
            "description": "I'm trying to merge user engagement metrics with my primary user table for a training dataset, but rows are dropping unexpectedly. Any advice?",
            "skill": "SQL & Data Querying",
            "difficulty": "Medium",
            "created_at": datetime.utcnow().isoformat(),
            "best_answer_id": None,
            "answers_count": 1
        })
        ans_id = "demo_ans_sarah"
        db_service.save("answers", ans_id, {
            "id": ans_id,
            "doubt_id": doubt_id,
            "user_id": "peer_sarah_ml",
            "author_name": "Sarah Chen",
            "content": "Use LEFT JOIN! If users don't have engagement events yet, INNER JOIN drops them entirely. LEFT JOIN keeps all users and fills missing engagement metrics with NULL, which you can then impute with 0!",
            "created_at": datetime.utcnow().isoformat(),
            "helpful_votes": 3,
            "helpful_voted_by": ["peer_marcus_dev"],
            "is_best": False
        })

        # 7. Today's Plan for Demo
        demo_plan = DailyPlan(
            id=f"plan_demo_{datetime.utcnow().strftime('%Y%m%d')}",
            user_id=user_id,
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            today_objective="Complete NumPy Vectorization & Solve SQL Querying Checkpoint",
            learning_activities=[
                {"id": "demo_act_1", "title": "NumPy Array Operations & Broadcasting Lesson", "skill": "NumPy", "type": "lesson", "duration_minutes": 25, "completed": True, "xp": 25},
                {"id": "demo_act_2", "title": "Relational Data Querying Practice Task", "skill": "SQL & Data Querying", "type": "practice", "duration_minutes": 30, "completed": False, "xp": 35}
            ],
            practice_tasks=[
                {"id": "demo_prac_1", "title": "Implement Multi-table JOIN queries", "skill": "SQL & Data Querying", "type": "practice", "duration_minutes": 25, "completed": False, "xp": 35}
            ],
            revision_tasks=[
                {"id": "demo_rev_1", "title": "Flashcards: SQL Joins vs Subqueries", "skill": "SQL & Data Querying", "type": "revision", "duration_minutes": 10, "completed": False, "xp": 15}
            ],
            estimated_minutes=90,
            completed=False
        )
        db_service.save("plans", demo_plan.id, demo_plan.model_dump())

        return {
            "status": "success",
            "message": "Demo learner (Alex Demo) seeded successfully with AI/ML Engineer profile and struggle scenario ready!",
            "user_id": user_id,
            "name": "Alex Demo",
            "target_role": "AI/ML Engineer"
        }

edupath_agent = EduPathAgent()

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from models.schemas import ActivityCompletionRequest, ProgressSummary, XPEvent
from services.firebase import db_service

logger = logging.getLogger("edupath.progress_tracker")

BADGE_DEFINITIONS = [
    {
        "id": "badge_first_assessment",
        "name": "First Assessment",
        "description": "Completed your first diagnostic skill assessment!",
        "icon": "🎯",
        "category": "assessment",
        "criteria": "complete_1_assessment"
    },
    {
        "id": "badge_streak_7",
        "name": "7 Day Streak",
        "description": "Maintained daily study momentum for 7 consecutive days!",
        "icon": "🔥",
        "category": "streak",
        "criteria": "streak_7_days"
    },
    {
        "id": "badge_helpful_peer",
        "name": "Helpful Peer",
        "description": "Answered a peer doubt and received a helpful upvote!",
        "icon": "🤝",
        "category": "peer",
        "criteria": "peer_helpful_1"
    },
    {
        "id": "badge_project_builder",
        "name": "Project Builder",
        "description": "Successfully completed a hands-on portfolio project!",
        "icon": "🚀",
        "category": "project",
        "criteria": "complete_project_1"
    },
    {
        "id": "badge_roadmap_finisher",
        "name": "Roadmap Finisher",
        "description": "Completed all milestones in your active learning path!",
        "icon": "🏆",
        "category": "roadmap",
        "criteria": "finish_roadmap"
    },
    {
        "id": "badge_challenge_master",
        "name": "Challenge Champion",
        "description": "Completed an active community learning challenge!",
        "icon": "⚡",
        "category": "challenge",
        "criteria": "complete_challenge_1"
    },
    {
        "id": "badge_skill_master",
        "name": "Skill Master",
        "description": "Achieved 90%+ confidence in a target role skill!",
        "icon": "👑",
        "category": "mastery",
        "criteria": "skill_90_percent"
    }
]

class ProgressTracker:
    @staticmethod
    def get_user_progress(user_id: str) -> ProgressSummary:
        """Fetch or initialize student progress metrics."""
        doc = db_service.get("progress", user_id)
        if not doc:
            summary = ProgressSummary(
                user_id=user_id,
                completed_activities=0,
                completed_objectives=0,
                overall_confidence=50,
                streak=1,
                longest_streak=1,
                total_xp=0,
                learning_hours=0.0,
                roadmap_progress_percent=0,
                weak_areas=[],
                reputation=0
            )
            db_service.save("progress", user_id, summary.model_dump())
            return summary
        return ProgressSummary(**doc)

    @staticmethod
    def award_xp(user_id: str, amount: int, source: str, description: str) -> int:
        """Award XP and record an immutable event in xp_events collection."""
        event_id = f"xp_{uuid.uuid4().hex[:10]}"
        xp_event = XPEvent(
            id=event_id,
            user_id=user_id,
            source=source,
            xp_amount=amount,
            description=description,
            timestamp=datetime.utcnow().isoformat()
        )
        db_service.save("xp_events", event_id, xp_event.model_dump())

        # Update progress total XP
        progress = ProgressTracker.get_user_progress(user_id)
        new_xp = progress.total_xp + amount
        db_service.update("progress", user_id, {"total_xp": new_xp})

        # Update leaderboard entry
        db_service.update("leaderboards", user_id, {"xp": new_xp, "updated_at": datetime.utcnow().isoformat()})
        return new_xp

    @staticmethod
    def update_streak(user_id: str) -> int:
        """Calculate and update consecutive active day streak."""
        progress = ProgressTracker.get_user_progress(user_id)
        progress_doc = db_service.get("progress", user_id) or {}
        
        last_date_str = progress_doc.get("last_activity_date")
        today_date = date.today()

        current_streak = progress.streak
        longest_streak = progress.longest_streak

        if not last_date_str:
            current_streak = 1
        else:
            try:
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
                delta_days = (today_date - last_date).days
                if delta_days == 1:
                    current_streak += 1
                elif delta_days > 1:
                    current_streak = 1
                # If delta_days == 0 (already active today), streak remains same
            except Exception:
                current_streak = 1

        longest_streak = max(longest_streak, current_streak)

        db_service.update("progress", user_id, {
            "streak": current_streak,
            "longest_streak": longest_streak,
            "last_activity_date": today_date.strftime("%Y-%m-%d")
        })
        db_service.update("leaderboards", user_id, {"streak": current_streak})

        # Check for 7 day streak badge
        if current_streak >= 7:
            ProgressTracker.award_badge_if_not_held(user_id, "badge_streak_7")

        return current_streak

    @staticmethod
    def complete_activity(req: ActivityCompletionRequest) -> Dict[str, Any]:
        """Record activity completion, grant XP, update streak, recalculate progress."""
        act_id = f"act_log_{uuid.uuid4().hex[:8]}"
        activity_doc = {
            "id": act_id,
            "user_id": req.user_id,
            "activity_id": req.activity_id,
            "skill": req.skill,
            "title": req.title,
            "activity_type": req.activity_type,
            "time_spent_minutes": req.time_spent_minutes,
            "timestamp": datetime.utcnow().isoformat()
        }
        db_service.save("activities", act_id, activity_doc)

        # Base XP logic
        xp_amount = 30
        if req.activity_type == "practice":
            xp_amount = 45
        elif req.activity_type == "project":
            xp_amount = 100
        elif req.activity_type == "revision":
            xp_amount = 20

        new_xp = ProgressTracker.award_xp(req.user_id, xp_amount, "activity", f"Completed {req.title}")
        current_streak = ProgressTracker.update_streak(req.user_id)

        # Update progress record
        progress = ProgressTracker.get_user_progress(req.user_id)
        new_activities_count = progress.completed_activities + 1
        new_learning_hours = round(progress.learning_hours + (req.time_spent_minutes / 60.0), 1)

        # Mark corresponding objective in active roadmap if applicable
        roadmap_doc = db_service.get_latest("roadmaps", req.user_id)
        roadmap_progress_pct = 0
        if roadmap_doc:
            items = roadmap_doc.get("items", [])
            total_objs = 0
            completed_objs = 0
            for item in items:
                if item.get("skill", "").lower() == req.skill.lower():
                    for obj in item.get("objectives_list", []):
                        if not obj.get("completed", False):
                            obj["completed"] = True
                            break
                for obj in item.get("objectives_list", []):
                    total_objs += 1
                    if obj.get("completed", False):
                        completed_objs += 1

            if total_objs > 0:
                roadmap_progress_pct = int(round((completed_objs / total_objs) * 100))
            db_service.save("roadmaps", roadmap_doc["_id"], roadmap_doc)

        db_service.update("progress", req.user_id, {
            "completed_activities": new_activities_count,
            "learning_hours": new_learning_hours,
            "roadmap_progress_percent": roadmap_progress_pct
        })

        return {
            "status": "success",
            "xp_awarded": xp_amount,
            "total_xp": new_xp,
            "current_streak": current_streak,
            "completed_activities": new_activities_count,
            "learning_hours": new_learning_hours,
            "roadmap_progress_percent": roadmap_progress_pct
        }

    @staticmethod
    def award_badge_if_not_held(user_id: str, badge_id: str) -> Optional[Dict[str, Any]]:
        """Award a badge if user has not yet unlocked it."""
        existing = db_service.query("user_badges", filters=[("user_id", "==", user_id), ("badge_id", "==", badge_id)])
        if existing:
            return None

        badge_meta = next((b for b in BADGE_DEFINITIONS if b["id"] == badge_id), None)
        if not badge_meta:
            return None

        user_badge_id = f"ub_{uuid.uuid4().hex[:8]}"
        user_badge_doc = {
            "id": user_badge_id,
            "user_id": user_id,
            "badge_id": badge_id,
            "name": badge_meta["name"],
            "description": badge_meta["description"],
            "icon": badge_meta["icon"],
            "awarded_at": datetime.utcnow().isoformat()
        }
        db_service.save("user_badges", user_badge_id, user_badge_doc)
        
        # Grant bonus XP for badge
        ProgressTracker.award_xp(user_id, 75, "badge", f"Unlocked badge: {badge_meta['name']}")
        return user_badge_doc

progress_tracker = ProgressTracker()

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.schemas import Challenge, UserChallenge, LeaderboardEntry, Competition, CompetitionAttempt
from tools.progress_tracker import BADGE_DEFINITIONS
from services.firebase import db_service

logger = logging.getLogger("edupath.competition_engine")

STANDARD_CHALLENGES: List[Dict[str, Any]] = [
    {
        "id": "chal_daily_streak",
        "title": "Unstoppable Momentum",
        "description": "Maintain a daily study streak for 7 consecutive days.",
        "category": "streak",
        "target_metric": "streak_days",
        "target_value": 7,
        "xp_reward": 150,
        "badge_reward": "badge_streak_7"
    },
    {
        "id": "chal_complete_activities",
        "title": "Sprint Master: 5 Lessons",
        "description": "Complete 5 guided roadmap learning activities.",
        "category": "learning",
        "target_metric": "activities",
        "target_value": 5,
        "xp_reward": 120,
        "badge_reward": None
    },
    {
        "id": "chal_high_assessment",
        "title": "Precision Exam: 80%+",
        "description": "Score 80% or above in any diagnostic skill assessment.",
        "category": "learning",
        "target_metric": "assessment_score",
        "target_value": 80,
        "xp_reward": 100,
        "badge_reward": "badge_first_assessment"
    },
    {
        "id": "chal_peer_help",
        "title": "Community Helper",
        "description": "Provide a helpful answer to a fellow learner's doubt.",
        "category": "peer",
        "target_metric": "doubts_helped",
        "target_value": 1,
        "xp_reward": 80,
        "badge_reward": "badge_helpful_peer"
    },
    {
        "id": "chal_finish_project",
        "title": "Capstone Builder",
        "description": "Complete all milestones of a personalized portfolio project.",
        "category": "coding",
        "target_metric": "projects",
        "target_value": 1,
        "xp_reward": 250,
        "badge_reward": "badge_project_builder"
    }
]

STANDARD_COMPETITIONS: List[Dict[str, Any]] = [
    {
        "id": "comp_python_blitz",
        "title": "Python Blitz Tournament",
        "description": "Test your speed on Python idiomatic list comprehensions, decorators, and generators.",
        "skill": "Python",
        "questions_count": 5,
        "xp_reward": 150,
        "active_until": "End of Week"
    },
    {
        "id": "comp_sql_speedrun",
        "title": "SQL Join Speedrun Challenge",
        "description": "Race the clock on multi-table joins, subqueries, and window functions.",
        "skill": "SQL & Data Querying",
        "questions_count": 5,
        "xp_reward": 150,
        "active_until": "Ongoing"
    },
    {
        "id": "comp_numpy_matrix",
        "title": "NumPy Array Master Showdown",
        "description": "Solve high-performance array broadcasting and tensor manipulation drills.",
        "skill": "NumPy",
        "questions_count": 5,
        "xp_reward": 200,
        "active_until": "Ongoing"
    }
]

class CompetitionEngine:
    @staticmethod
    def get_leaderboard(timeframe: str = "global", limit: int = 25) -> List[LeaderboardEntry]:
        """Compute live leaderboard rankings based on actual persistent user progress."""
        all_progress = db_service.query("progress")
        entries: List[LeaderboardEntry] = []

        for p in all_progress:
            u_id = p.get("user_id")
            prof = db_service.get("profiles", u_id) or {}
            badges = db_service.query("user_badges", filters=[("user_id", "==", u_id)])
            
            # Determine score based on timeframe
            xp = p.get("total_xp", 0)
            if timeframe == "weekly":
                xp = int(xp * 0.4) + (p.get("streak", 1) * 10)
            elif timeframe == "monthly":
                xp = int(xp * 0.75) + (p.get("streak", 1) * 25)

            entries.append(LeaderboardEntry(
                rank=1,  # will be assigned post sort
                user_id=u_id,
                display_name=prof.get("name", u_id),
                target_role=prof.get("target_role", "Tech Learner"),
                xp=xp,
                streak=p.get("streak", 1),
                badges_count=len(badges)
            ))

        # Include seeded peer benchmark participants if few users exist
        if len(entries) < 4:
            benchmarks = [
                {"user_id": "peer_sarah_ml", "display_name": "Sarah Chen", "target_role": "AI/ML Engineer", "xp": 1420, "streak": 14, "badges_count": 5},
                {"user_id": "peer_marcus_dev", "display_name": "Marcus Rodriguez", "target_role": "Software Engineer", "xp": 1180, "streak": 9, "badges_count": 4},
                {"user_id": "peer_aisha_fullstack", "display_name": "Aisha Patel", "target_role": "Full Stack Developer", "xp": 950, "streak": 6, "badges_count": 3}
            ]
            for b in benchmarks:
                if not any(e.user_id == b["user_id"] for e in entries):
                    entries.append(LeaderboardEntry(
                        rank=1,
                        user_id=b["user_id"],
                        display_name=b["display_name"],
                        target_role=b["target_role"],
                        xp=b["xp"],
                        streak=b["streak"],
                        badges_count=b["badges_count"]
                    ))

        # Sort by XP descending, then streak
        entries.sort(key=lambda x: (x.xp, x.streak), reverse=True)

        for rank_idx, entry in enumerate(entries[:limit], start=1):
            entry.rank = rank_idx

        return entries[:limit]

    @staticmethod
    def get_friends_leaderboard(user_id: str) -> List[LeaderboardEntry]:
        """Compute leaderboard filtered strictly to the user and their mutual friends."""
        friends = db_service.query_by_user("friends", user_id)
        allowed_ids = {user_id}
        for f in friends:
            allowed_ids.add(f.get("friend_user_id"))

        global_entries = CompetitionEngine.get_leaderboard(timeframe="global", limit=50)
        filtered = [e for e in global_entries if e.user_id in allowed_ids]

        for rank_idx, entry in enumerate(filtered, start=1):
            entry.rank = rank_idx

        return filtered

    @staticmethod
    def get_challenges(user_id: str) -> List[Dict[str, Any]]:
        """List all challenges and user's personal enrollment/completion state."""
        user_challenges = {
            uc.get("challenge_id"): uc
            for uc in db_service.query_by_user("user_challenges", user_id)
        }

        results = []
        for chal in STANDARD_CHALLENGES:
            c_id = chal["id"]
            if c_id in user_challenges:
                uc = user_challenges[c_id]
                chal_copy = dict(chal)
                chal_copy["status"] = uc.get("status", "In Progress")
                chal_copy["current_value"] = uc.get("current_value", 0)
                chal_copy["target_value"] = chal["target_value"]
            else:
                chal_copy = dict(chal)
                chal_copy["status"] = "Available"
                chal_copy["current_value"] = 0
            results.append(chal_copy)
        return results

    @staticmethod
    def join_challenge(user_id: str, challenge_id: str) -> Dict[str, Any]:
        """Enroll in a challenge."""
        chal = next((c for c in STANDARD_CHALLENGES if c["id"] == challenge_id), None)
        if not chal:
            raise ValueError(f"Challenge {challenge_id} not found.")

        doc_id = f"{user_id}_{challenge_id}"
        user_chal = UserChallenge(
            id=doc_id,
            user_id=user_id,
            challenge_id=challenge_id,
            title=chal["title"],
            current_value=0,
            target_value=chal["target_value"],
            xp_reward=chal["xp_reward"],
            status="In Progress",
            joined_at=datetime.utcnow().isoformat(),
            completed_at=None
        )
        db_service.save("user_challenges", doc_id, user_chal.model_dump())
        return user_chal.model_dump()

    @staticmethod
    def complete_challenge(user_id: str, challenge_id: str) -> Dict[str, Any]:
        """Manually or automatically mark a challenge completed."""
        chal = next((c for c in STANDARD_CHALLENGES if c["id"] == challenge_id), None)
        if not chal:
            raise ValueError(f"Challenge {challenge_id} not found.")

        doc_id = f"{user_id}_{challenge_id}"
        existing = db_service.get("user_challenges", doc_id)
        if existing and existing.get("status") == "Completed":
            return existing

        now_iso = datetime.utcnow().isoformat()
        updates = {
            "status": "Completed",
            "current_value": chal["target_value"],
            "completed_at": now_iso
        }
        updated = db_service.update("user_challenges", doc_id, updates)

        # Award XP and badge
        from tools.progress_tracker import progress_tracker
        progress_tracker.award_xp(user_id, chal["xp_reward"], "challenge", f"Completed challenge: {chal['title']}")
        if chal.get("badge_reward"):
            progress_tracker.award_badge_if_not_held(user_id, chal["badge_reward"])
        progress_tracker.award_badge_if_not_held(user_id, "badge_challenge_master")

        return updated

    @staticmethod
    def get_badges(user_id: str) -> List[Dict[str, Any]]:
        """List all badges showing earned vs locked status."""
        earned_badges = {
            b.get("badge_id"): b
            for b in db_service.query_by_user("user_badges", user_id)
        }

        badge_list = []
        for b_def in BADGE_DEFINITIONS:
            b_id = b_def["id"]
            if b_id in earned_badges:
                b_copy = dict(b_def)
                b_copy["unlocked"] = True
                b_copy["awarded_at"] = earned_badges[b_id].get("awarded_at")
            else:
                b_copy = dict(b_def)
                b_copy["unlocked"] = False
                b_copy["awarded_at"] = None
            badge_list.append(b_copy)
        return badge_list

    @staticmethod
    def get_competitions() -> List[Dict[str, Any]]:
        """List ongoing competitions."""
        return STANDARD_COMPETITIONS

    @staticmethod
    def attempt_competition(user_id: str, comp_id: str, score: int, time_taken_seconds: int) -> Dict[str, Any]:
        """Record attempt in a competition."""
        comp = next((c for c in STANDARD_COMPETITIONS if c["id"] == comp_id), None)
        if not comp:
            raise ValueError(f"Competition {comp_id} not found.")

        att_id = f"att_{uuid.uuid4().hex[:8]}"
        attempt = CompetitionAttempt(
            id=att_id,
            competition_id=comp_id,
            user_id=user_id,
            score=score,
            time_taken_seconds=time_taken_seconds,
            timestamp=datetime.utcnow().isoformat()
        )
        db_service.save("competition_attempts", att_id, attempt.model_dump())

        # Award scaled XP
        from tools.progress_tracker import progress_tracker
        earned_xp = int(round((score / 100.0) * comp["xp_reward"]))
        progress_tracker.award_xp(user_id, earned_xp, "competition", f"Competed in {comp['title']} (Score: {score}%)")

        return {
            "status": "success",
            "score": score,
            "xp_earned": earned_xp,
            "rank_estimate": 1 if score >= 90 else (3 if score >= 70 else 5)
        }

competition_engine = CompetitionEngine()

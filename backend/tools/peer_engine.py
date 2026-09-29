import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.schemas import (
    FriendRequest, Friend, Doubt, DoubtAnswer, StudyGroup, CommunityPost, CommunityComment
)
from services.firebase import db_service

logger = logging.getLogger("edupath.peer_engine")

class PeerEngine:
    # --- Peer Discovery & Matching ---
    @staticmethod
    def get_peer_recommendations(user_id: str) -> List[Dict[str, Any]]:
        """Find peers with complementary skills (e.g. they excel at skills you are building)."""
        all_profiles = db_service.query("profiles")
        my_profile = db_service.get("profiles", user_id) or {}
        my_skills = set(s.lower() for s in my_profile.get("current_skills", []))
        my_role = my_profile.get("target_role", "")

        candidates = []
        for p in all_profiles:
            other_id = p.get("user_id")
            if other_id == user_id:
                continue

            their_skills = p.get("current_skills", [])
            complementary = [s for s in their_skills if s.lower() not in my_skills]
            shared = [s for s in their_skills if s.lower() in my_skills]

            # Calculate match reason
            match_reason = f"Strong in {', '.join(complementary[:2]) if complementary else 'Software Engineering'} which complements your path."
            if p.get("target_role") == my_role:
                match_reason += f" Also pursuing {my_role}!"

            candidates.append({
                "user_id": other_id,
                "name": p.get("name", "Peer"),
                "target_role": p.get("target_role", "Tech Learner"),
                "skills": their_skills,
                "experience": p.get("experience", "Student"),
                "hours_per_week": p.get("hours_per_week", 10),
                "match_reason": match_reason,
                "complementary_skills": complementary[:3],
                "shared_skills": shared[:3]
            })

        # If no other profiles exist yet, provide realistic peer candidates
        if not candidates:
            candidates = [
                {
                    "user_id": "peer_sarah_ml",
                    "name": "Sarah Chen",
                    "target_role": "AI/ML Engineer",
                    "skills": ["Python", "NumPy", "Pandas", "Scikit-Learn", "PyTorch"],
                    "experience": "ML Research Assistant",
                    "hours_per_week": 15,
                    "match_reason": "High proficiency in NumPy & Pandas data pipelines — perfect mentor for your data wrangling gap.",
                    "complementary_skills": ["NumPy", "PyTorch"],
                    "shared_skills": ["Python"]
                },
                {
                    "user_id": "peer_marcus_dev",
                    "name": "Marcus Rodriguez",
                    "target_role": "Software Engineer",
                    "skills": ["C++", "Python", "Data Structures", "System Design", "SQL"],
                    "experience": "Open Source Contributor",
                    "hours_per_week": 12,
                    "match_reason": "Excels in algorithmic optimization and relational database querying.",
                    "complementary_skills": ["Data Structures", "SQL"],
                    "shared_skills": ["C++", "Python"]
                },
                {
                    "user_id": "peer_aisha_fullstack",
                    "name": "Aisha Patel",
                    "target_role": "Full Stack Developer",
                    "skills": ["HTML5", "CSS3", "JavaScript", "FastAPI", "React"],
                    "experience": "Frontend Bootcamp Graduate",
                    "hours_per_week": 10,
                    "match_reason": "Great peer for web interface building and API integration drills.",
                    "complementary_skills": ["CSS3", "JavaScript"],
                    "shared_skills": ["HTML5"]
                }
            ]
        return candidates

    # --- Friends System ---
    @staticmethod
    def send_friend_request(from_user_id: str, to_user_id: str) -> Dict[str, Any]:
        """Send a friend request."""
        if from_user_id == to_user_id:
            raise ValueError("You cannot send a friend request to yourself.")

        # Check existing
        existing = db_service.query("friend_requests", filters=[
            ("from_user_id", "==", from_user_id),
            ("to_user_id", "==", to_user_id)
        ])
        if existing:
            return existing[0]

        from_profile = db_service.get("profiles", from_user_id) or {}
        req_id = f"freq_{uuid.uuid4().hex[:8]}"
        req = FriendRequest(
            id=req_id,
            from_user_id=from_user_id,
            from_name=from_profile.get("name", "Fellow Learner"),
            to_user_id=to_user_id,
            status="pending",
            created_at=datetime.utcnow().isoformat()
        )
        db_service.save("friend_requests", req_id, req.model_dump())
        return req.model_dump()

    @staticmethod
    def accept_friend_request(request_id: str, current_user_id: str) -> Dict[str, Any]:
        """Accept a friend request and create mutual friendship records."""
        req = db_service.get("friend_requests", request_id)
        if not req:
            raise ValueError(f"Friend request {request_id} not found.")

        if req.get("to_user_id") != current_user_id:
            raise ValueError("You can only accept requests directed to you.")

        # Update request status
        db_service.update("friend_requests", request_id, {"status": "accepted"})

        from_id = req["from_user_id"]
        to_id = req["to_user_id"]

        from_p = db_service.get("profiles", from_id) or {}
        to_p = db_service.get("profiles", to_id) or {}

        # Save mutual records in friends collection
        f1_id = f"friend_{from_id}_{to_id}"
        f1 = Friend(
            id=f1_id,
            user_id=from_id,
            friend_user_id=to_id,
            friend_name=to_p.get("name", "Peer"),
            friend_role=to_p.get("target_role", "Tech Learner"),
            friend_streak=1,
            friend_xp=50,
            created_at=datetime.utcnow().isoformat()
        )
        db_service.save("friends", f1_id, f1.model_dump())

        f2_id = f"friend_{to_id}_{from_id}"
        f2 = Friend(
            id=f2_id,
            user_id=to_id,
            friend_user_id=from_id,
            friend_name=from_p.get("name", "Peer"),
            friend_role=from_p.get("target_role", "Tech Learner"),
            friend_streak=1,
            friend_xp=50,
            created_at=datetime.utcnow().isoformat()
        )
        db_service.save("friends", f2_id, f2.model_dump())

        return {"status": "accepted", "friend_user_id": from_id}

    @staticmethod
    def list_friends(user_id: str) -> List[Dict[str, Any]]:
        """List active friends for a user."""
        return db_service.query_by_user("friends", user_id)

    @staticmethod
    def list_pending_requests(user_id: str) -> List[Dict[str, Any]]:
        """List incoming pending friend requests."""
        return db_service.query("friend_requests", filters=[("to_user_id", "==", user_id), ("status", "==", "pending")])

    # --- Doubt Forum ---
    @staticmethod
    def create_doubt(user_id: str, title: str, description: str, skill: str, difficulty: str = "Medium") -> Dict[str, Any]:
        """Post a new doubt to the peer community."""
        profile = db_service.get("profiles", user_id) or {}
        doubt_id = f"doubt_{uuid.uuid4().hex[:8]}"
        doubt = Doubt(
            id=doubt_id,
            user_id=user_id,
            author_name=profile.get("name", "Anonymous Learner"),
            title=title,
            description=description,
            skill=skill,
            difficulty=difficulty,
            created_at=datetime.utcnow().isoformat(),
            best_answer_id=None,
            answers_count=0
        )
        db_service.save("doubts", doubt_id, doubt.model_dump())
        return doubt.model_dump()

    @staticmethod
    def list_doubts(skill: Optional[str] = None) -> List[Dict[str, Any]]:
        """List doubts, optionally filtered by skill."""
        filters = []
        if skill:
            filters.append(("skill", "==", skill))
        doubts = db_service.query("doubts", filters=filters, order_by="created_at", descending=True)
        return doubts

    @staticmethod
    def answer_doubt(doubt_id: str, user_id: str, content: str) -> Dict[str, Any]:
        """Submit a peer answer to a doubt."""
        doubt = db_service.get("doubts", doubt_id)
        if not doubt:
            raise ValueError(f"Doubt {doubt_id} not found.")

        profile = db_service.get("profiles", user_id) or {}
        ans_id = f"ans_{uuid.uuid4().hex[:8]}"
        ans = DoubtAnswer(
            id=ans_id,
            doubt_id=doubt_id,
            user_id=user_id,
            author_name=profile.get("name", "Peer Contributor"),
            content=content,
            created_at=datetime.utcnow().isoformat(),
            helpful_votes=0,
            helpful_voted_by=[],
            is_best=False
        )
        db_service.save("answers", ans_id, ans.model_dump())

        # Increment answers_count
        new_count = doubt.get("answers_count", 0) + 1
        db_service.update("doubts", doubt_id, {"answers_count": new_count})

        # Award base XP for answering
        from tools.progress_tracker import progress_tracker
        progress_tracker.award_xp(user_id, 20, "peer_answer", f"Answered peer doubt: {doubt.get('title')[:30]}")

        return ans.model_dump()

    @staticmethod
    def list_answers_for_doubt(doubt_id: str) -> List[Dict[str, Any]]:
        """Retrieve all peer answers for a specific doubt."""
        return db_service.query("answers", filters=[("doubt_id", "==", doubt_id)], order_by="created_at", descending=False)

    @staticmethod
    def vote_helpful(answer_id: str, user_id: str) -> Dict[str, Any]:
        """Upvote an answer as helpful."""
        ans = db_service.get("answers", answer_id)
        if not ans:
            raise ValueError(f"Answer {answer_id} not found.")

        voters = ans.get("helpful_voted_by", [])
        if user_id in voters:
            return ans  # Already voted

        voters.append(user_id)
        new_votes = ans.get("helpful_votes", 0) + 1
        updated = db_service.update("answers", answer_id, {
            "helpful_votes": new_votes,
            "helpful_voted_by": voters
        })

        # Boost author reputation & award XP
        author_id = ans.get("user_id")
        if author_id and author_id != user_id:
            from tools.progress_tracker import progress_tracker
            progress_tracker.award_xp(author_id, 15, "helpful_vote", "Received a helpful vote on peer answer")
            progress = db_service.get("progress", author_id) or {}
            new_rep = progress.get("reputation", 0) + 5
            db_service.update("progress", author_id, {"reputation": new_rep})
            # Check for helpful peer badge
            progress_tracker.award_badge_if_not_held(author_id, "badge_helpful_peer")

        return updated

    @staticmethod
    def mark_best_answer(doubt_id: str, answer_id: str, current_user_id: str) -> Dict[str, Any]:
        """
        Mark an answer as the Best Answer.
        CRITICAL PERMISSION: Only the doubt author can mark best answer.
        Cannot mark own answer as best.
        """
        doubt = db_service.get("doubts", doubt_id)
        if not doubt:
            raise ValueError(f"Doubt {doubt_id} not found.")

        if doubt.get("user_id") != current_user_id:
            raise PermissionError("Only the author of this doubt can mark an answer as the Best Answer.")

        ans = db_service.get("answers", answer_id)
        if not ans or ans.get("doubt_id") != doubt_id:
            raise ValueError("Answer does not belong to this doubt.")

        if ans.get("user_id") == current_user_id:
            raise ValueError("You cannot mark your own answer as the Best Answer.")

        # Clear existing best answers for this doubt
        existing_answers = db_service.query("answers", filters=[("doubt_id", "==", doubt_id)])
        for a in existing_answers:
            if a.get("is_best", False):
                db_service.update("answers", a["_id"], {"is_best": False})

        # Mark this answer as best
        updated_ans = db_service.update("answers", answer_id, {"is_best": True})
        db_service.update("doubts", doubt_id, {"best_answer_id": answer_id})

        # Award bonus XP and reputation to answer author
        author_id = ans.get("user_id")
        if author_id:
            from tools.progress_tracker import progress_tracker
            progress_tracker.award_xp(author_id, 50, "best_answer", f"Awarded Best Answer on doubt: {doubt.get('title')[:30]}")
            progress = db_service.get("progress", author_id) or {}
            new_rep = progress.get("reputation", 0) + 20
            db_service.update("progress", author_id, {"reputation": new_rep})

        return updated_ans

    # --- Study Groups ---
    @staticmethod
    def create_group(user_id: str, name: str, description: str, skills: List[str], target_role: str = "All Roles") -> Dict[str, Any]:
        """Create a collaborative study group."""
        profile = db_service.get("profiles", user_id) or {}
        grp_id = f"grp_{uuid.uuid4().hex[:8]}"
        group = StudyGroup(
            id=grp_id,
            name=name,
            description=description,
            skills=skills,
            target_role=target_role,
            creator_id=user_id,
            creator_name=profile.get("name", "Founder"),
            members=[{"user_id": user_id, "name": profile.get("name", "Founder"), "role": "admin"}],
            created_at=datetime.utcnow().isoformat()
        )
        db_service.save("groups", grp_id, group.model_dump())
        return group.model_dump()

    @staticmethod
    def list_groups() -> List[Dict[str, Any]]:
        """List all study groups."""
        return db_service.query("groups", order_by="created_at", descending=True)

    @staticmethod
    def join_group(group_id: str, user_id: str) -> Dict[str, Any]:
        """Join a study group."""
        group = db_service.get("groups", group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found.")

        members = group.get("members", [])
        if any(m.get("user_id") == user_id for m in members):
            return group

        profile = db_service.get("profiles", user_id) or {}
        members.append({"user_id": user_id, "name": profile.get("name", "Member"), "role": "member"})
        return db_service.update("groups", group_id, {"members": members})

    @staticmethod
    def leave_group(group_id: str, user_id: str) -> Dict[str, Any]:
        """Leave a study group."""
        group = db_service.get("groups", group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found.")

        members = [m for m in group.get("members", []) if m.get("user_id") != user_id]
        return db_service.update("groups", group_id, {"members": members})

    # --- Community Posts ---
    @staticmethod
    def create_post(user_id: str, category: str, title: str, content: str) -> Dict[str, Any]:
        """Create a post in the student community."""
        profile = db_service.get("profiles", user_id) or {}
        post_id = f"post_{uuid.uuid4().hex[:8]}"
        post = CommunityPost(
            id=post_id,
            user_id=user_id,
            author_name=profile.get("name", "Learner"),
            category=category,
            title=title,
            content=content,
            likes=0,
            liked_by=[],
            comments_count=0,
            created_at=datetime.utcnow().isoformat()
        )
        db_service.save("community_posts", post_id, post.model_dump())
        return post.model_dump()

    @staticmethod
    def list_posts(category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List community posts, optionally filtered by category."""
        filters = []
        if category and category != "All":
            filters.append(("category", "==", category))
        return db_service.query("community_posts", filters=filters, order_by="created_at", descending=True)

    @staticmethod
    def add_comment(post_id: str, user_id: str, content: str) -> Dict[str, Any]:
        """Add a comment to a community post."""
        post = db_service.get("community_posts", post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found.")

        profile = db_service.get("profiles", user_id) or {}
        c_id = f"comm_{uuid.uuid4().hex[:8]}"
        comment = CommunityComment(
            id=c_id,
            post_id=post_id,
            user_id=user_id,
            author_name=profile.get("name", "Learner"),
            content=content,
            created_at=datetime.utcnow().isoformat()
        )
        db_service.save("community_comments", c_id, comment.model_dump())

        # Increment comment counter
        new_count = post.get("comments_count", 0) + 1
        db_service.update("community_posts", post_id, {"comments_count": new_count})
        return comment.model_dump()

    @staticmethod
    def list_comments_for_post(post_id: str) -> List[Dict[str, Any]]:
        """Retrieve all comments on a post."""
        return db_service.query("community_comments", filters=[("post_id", "==", post_id)], order_by="created_at", descending=False)

peer_engine = PeerEngine()

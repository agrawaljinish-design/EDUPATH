import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.schemas import StruggleEvent, Roadmap, RoadmapItem, LearningObjective
from tools.resource_search import resource_search
from services.firebase import db_service

logger = logging.getLogger("edupath.struggle_detector")

class StruggleDetector:
    @staticmethod
    def detect_and_intervene(
        user_id: str,
        skill: str,
        topic: str = "",
        trigger_type: str = "im_stuck_button",
        details: str = ""
    ) -> StruggleEvent:
        """
        Analyze struggle, generate explanation, insert revision, and dynamically adapt active roadmap.
        """
        if not topic:
            topic = f"Foundational operations in {skill}"

        # 1. Fetch current roadmap
        roadmap_doc = db_service.get_latest("roadmaps", user_id)
        before_roadmap_summary: List[str] = []
        after_roadmap_summary: List[str] = []

        active_roadmap: Optional[Roadmap] = None
        if roadmap_doc:
            active_roadmap = Roadmap(**roadmap_doc)
            before_roadmap_summary = [item.skill for item in active_roadmap.items]

        # 2. Pedagogical explanation of why the learner might be stuck
        explanation = (
            f"Struggle detected in **{skill}** ({topic}). "
            f"When tackling {skill}, learners frequently stumble on abstract syntax or non-intuitive edge cases. "
            f"To overcome this cognitive block, we pause advance modules to isolate the core concept with a simplified model."
        )

        easier_task = f"Complete guided 10-minute micro-exercise on {skill} ({topic}) with step-by-step visual hints."
        revision_task = f"Review 5 high-yield flashcards and foundational rules for {skill} ({topic})."

        # 3. Insert into revision_queue
        rev_id = f"rev_{uuid.uuid4().hex[:8]}"
        revision_payload = {
            "id": rev_id,
            "user_id": user_id,
            "skill": skill,
            "topic": topic,
            "last_reviewed": None,
            "next_review": datetime.utcnow().isoformat(),
            "performance": 30,
            "interval_days": 1,
            "repetition_count": 0,
            "due": True,
            "flashcards": [
                {"front": f"What is the key principle of {topic} in {skill}?", "back": f"Breaking down the operation into simple verifiable steps before writing full code."},
                {"front": f"What common bug occurs in {topic}?", "back": "Unintended type mismatch or missing boundary condition."}
            ]
        }
        db_service.save("revision_queue", rev_id, revision_payload)

        # 4. Adaptive replanning: restructure the roadmap!
        if active_roadmap and active_roadmap.items:
            # Check if an adaptation item for this skill already exists
            already_adapted = any(i.skill == f"{skill} (Targeted Revision)" for i in active_roadmap.items)
            if not already_adapted:
                # Create an adaptive reinforcement module
                adapt_id = f"adapt_{uuid.uuid4().hex[:8]}"
                adaptive_item = RoadmapItem(
                    id=adapt_id,
                    skill=f"{skill} (Targeted Revision)",
                    priority="Critical",
                    objective=f"Reinforce {topic} & foundational syntax with low-friction practice",
                    objectives_list=[
                        LearningObjective(id=f"{adapt_id}_obj_1", title=f"Review visual guide on {topic}", completed=False),
                        LearningObjective(id=f"{adapt_id}_obj_2", title=f"Solve 2 guided bite-sized {skill} exercises", completed=False),
                        LearningObjective(id=f"{adapt_id}_obj_3", title=f"Pass checkpoint quiz on {skill}", completed=False)
                    ],
                    resources=resource_search.get_resources_for_skill(skill, count=2),
                    estimated_hours=2,
                    status="Needs Revision",
                    difficulty="Easy",
                    dependencies=[],
                    why_learning=f"Adaptive reinforcement inserted to unblock your mastery in {skill}.",
                    unlocked_skills=[skill],
                    is_adaptation=True
                )

                # Find index of current skill and insert adaptation right before it or at position 0
                insert_idx = 0
                for idx, it in enumerate(active_roadmap.items):
                    if skill.lower() in it.skill.lower() or it.skill.lower() in skill.lower():
                        insert_idx = idx
                        break

                active_roadmap.items.insert(insert_idx, adaptive_item)
                active_roadmap.version += 1
                active_roadmap.updated_at = datetime.utcnow().isoformat()
                active_roadmap.replan_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": f"Struggle in {skill}: {topic}",
                    "inserted_item": adaptive_item.skill
                })

                # Save updated roadmap to Firestore
                db_service.save("roadmaps", active_roadmap.id, active_roadmap.model_dump())
                after_roadmap_summary = [item.skill for item in active_roadmap.items]
            else:
                after_roadmap_summary = before_roadmap_summary
        else:
            after_roadmap_summary = [f"{skill} (Targeted Revision)", skill]

        # 5. Create Struggle Event
        event_id = f"struggle_{uuid.uuid4().hex[:8]}"
        event = StruggleEvent(
            id=event_id,
            user_id=user_id,
            skill=skill,
            topic=topic,
            trigger_type=trigger_type,
            explanation=explanation,
            prerequisite_skill=skill,
            before_roadmap_summary=before_roadmap_summary,
            after_roadmap_summary=after_roadmap_summary,
            intervention_action="Inserted targeted revision module & paused advanced modules until checkpoint completed",
            easier_practice_task=easier_task,
            revision_task=revision_task,
            timestamp=datetime.utcnow().isoformat()
        )

        db_service.save("struggle_events", event_id, event.model_dump())
        return event

struggle_detector = StruggleDetector()

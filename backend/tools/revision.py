import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from models.schemas import RevisionItem
from services.firebase import db_service

logger = logging.getLogger("edupath.revision")

DEFAULT_FLASHCARDS: Dict[str, List[Dict[str, str]]] = {
    "Python": [
        {"front": "What is the difference between a list and a tuple in Python?", "back": "Lists are mutable (can be changed); tuples are immutable and hashable if containing hashable items."},
        {"front": "What does the GIL (Global Interpreter Lock) do in CPython?", "back": "A mutex that prevents multiple native threads from executing Python bytecodes at once."},
        {"front": "How does `is` differ from `==`?", "back": "`is` checks identity (same memory address); `==` checks equality of values."}
    ],
    "SQL & Data Querying": [
        {"front": "What is the key difference between WHERE and HAVING?", "back": "WHERE filters individual rows before grouping; HAVING filters aggregated groups."},
        {"front": "What is an index and what is its primary trade-off?", "back": "Speeds up SELECT queries via B-Tree lookup, but slows down INSERT/UPDATE writes and uses extra disk storage."},
        {"front": "What is the result of joining on a column with NULLs?", "back": "NULL != NULL, so rows with NULL in join keys do not match in standard equality joins."}
    ],
    "NumPy": [
        {"front": "What does `array.shape` return?", "back": "A tuple representing the size of each dimension in the ndarray."},
        {"front": "Why is vectorization faster than Python for-loops?", "back": "It pushes iterations to compiled C/Fortran code and utilizes SIMD processor registers."}
    ],
    "Pandas": [
        {"front": "What is the difference between `.loc[]` and `.iloc[]`?", "back": "`.loc[]` indexes by label; `.iloc[]` indexes by integer position."},
        {"front": "How do you drop missing values in a DataFrame?", "back": "`df.dropna()` or fill them with `df.fillna(value)`."}
    ]
}

class RevisionEngine:
    @staticmethod
    def get_due_revisions(user_id: str) -> List[Dict[str, Any]]:
        """Retrieve items in user's revision queue."""
        items = db_service.query("revision_queue", filters=[("user_id", "==", user_id)])
        now_iso = datetime.utcnow().isoformat()
        for it in items:
            # Mark due if next_review is past
            it["due"] = it.get("next_review", "") <= now_iso
        return items

    @staticmethod
    def add_to_queue(user_id: str, skill: str, topic: str, performance: int = 50) -> Dict[str, Any]:
        """Add or update an item in the spaced repetition queue."""
        item_id = f"rev_{uuid.uuid4().hex[:8]}"
        flashcards = DEFAULT_FLASHCARDS.get(skill, [
            {"front": f"Core concept in {topic} ({skill})", "back": f"Fundamental rule and application for {topic}."},
            {"front": f"Common error to avoid in {topic}", "back": f"Pay attention to edge cases and input validation."}
        ])

        payload = {
            "id": item_id,
            "user_id": user_id,
            "skill": skill,
            "topic": topic,
            "last_reviewed": None,
            "next_review": datetime.utcnow().isoformat(),
            "performance": performance,
            "interval_days": 1,
            "repetition_count": 0,
            "due": True,
            "flashcards": flashcards
        }
        db_service.save("revision_queue", item_id, payload)
        return payload

    @staticmethod
    def record_review(user_id: str, item_id: str, score: int) -> Dict[str, Any]:
        """Record spaced repetition review and calculate next interval (SM-2 simplified)."""
        item = db_service.get("revision_queue", item_id)
        if not item:
            raise ValueError(f"Revision item {item_id} not found.")

        current_interval = item.get("interval_days", 1)
        repetition = item.get("repetition_count", 0)

        if score >= 80:
            # Multiplier on success
            new_interval = current_interval * 2 if repetition > 0 else 2
            repetition += 1
        elif score >= 60:
            new_interval = current_interval + 1
        else:
            # Reset on struggle
            new_interval = 1
            repetition = 0

        next_date = (datetime.utcnow() + timedelta(days=new_interval)).isoformat()

        updates = {
            "last_reviewed": datetime.utcnow().isoformat(),
            "next_review": next_date,
            "performance": score,
            "interval_days": new_interval,
            "repetition_count": repetition,
            "due": False
        }
        updated_doc = db_service.update("revision_queue", item_id, updates)
        return updated_doc

revision_engine = RevisionEngine()

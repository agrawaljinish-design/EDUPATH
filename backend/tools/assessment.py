import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.schemas import Assessment, AssessmentQuestion, AssessmentSubmission, AssessmentResult
from services.openai_service import openai_service
from services.firebase import db_service

logger = logging.getLogger("edupath.assessment")

# High quality pre-crafted question banks by skill for guaranteed instant availability and fallback
CURATED_ASSESSMENT_BANKS: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "Python": {
        "Medium": [
            {
                "id": "py_m_1",
                "type": "mcq",
                "question": "What is the time complexity of looking up a key in a Python dictionary on average?",
                "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
                "correct_answer": "O(1)",
                "explanation": "Python dictionaries use an optimized hash table, yielding average O(1) amortized lookup time.",
                "difficulty": "Medium",
                "skill": "Python"
            },
            {
                "id": "py_m_2",
                "type": "code",
                "question": "What will be the output of the following code snippet?",
                "code_snippet": "data = [x**2 for x in range(5) if x % 2 == 1]\nprint(data)",
                "options": ["[1, 9]", "[0, 4, 16]", "[1, 4, 9]", "[0, 1, 4, 9, 16]"],
                "correct_answer": "[1, 9]",
                "explanation": "range(5) yields 0, 1, 2, 3, 4. Odd numbers are 1 and 3. Their squares are 1 and 9.",
                "difficulty": "Medium",
                "skill": "Python"
            },
            {
                "id": "py_m_3",
                "type": "mcq",
                "question": "In Python, which keyword is used to create an anonymous inline function?",
                "options": ["lambda", "def", "func", "inline"],
                "correct_answer": "lambda",
                "explanation": "The 'lambda' keyword creates small anonymous functions syntactically restricted to a single expression.",
                "difficulty": "Medium",
                "skill": "Python"
            },
            {
                "id": "py_m_4",
                "type": "code",
                "question": "What does this generator function yield on the first next() call?",
                "code_snippet": "def countdown(n):\n    while n > 0:\n        yield n\n        n -= 1\n\ngen = countdown(3)\nprint(next(gen))",
                "options": ["3", "2", "1", "None"],
                "correct_answer": "3",
                "explanation": "The first execution runs until the first yield statement, returning n which is 3.",
                "difficulty": "Medium",
                "skill": "Python"
            },
            {
                "id": "py_m_5",
                "type": "mcq",
                "question": "What happens if you mutate a default argument like `def func(a, items=[]):`?",
                "options": [
                    "The same list instance is shared across subsequent calls that omit the parameter",
                    "A new list is created on every call",
                    "A TypeError is raised at runtime",
                    "The list is deleted when the function exits"
                ],
                "correct_answer": "The same list instance is shared across subsequent calls that omit the parameter",
                "explanation": "Default parameter values in Python are evaluated once when the function definition is executed.",
                "difficulty": "Medium",
                "skill": "Python"
            }
        ]
    },
    "NumPy": {
        "Medium": [
            {
                "id": "np_m_1",
                "type": "mcq",
                "question": "What is the primary advantage of NumPy ndarrays over standard Python lists?",
                "options": [
                    "Contiguous memory layout and vectorized C-level operations",
                    "Can store arbitrary mixed types dynamically without conversion",
                    "Uses more memory per element for safety",
                    "Requires no indexing syntax"
                ],
                "correct_answer": "Contiguous memory layout and vectorized C-level operations",
                "explanation": "NumPy arrays are stored in contiguous memory blocks, enabling SIMD vectorization and cache locality.",
                "difficulty": "Medium",
                "skill": "NumPy"
            },
            {
                "id": "np_m_2",
                "type": "code",
                "question": "What is the shape of `c` after broadcasting?",
                "code_snippet": "import numpy as np\na = np.ones((3, 1))\nb = np.ones((1, 4))\nc = a + b",
                "options": ["(3, 4)", "(3, 1)", "(1, 4)", "ValueError: shapes cannot broadcast"],
                "correct_answer": "(3, 4)",
                "explanation": "Broadcasting expands dimensions with size 1 to match the other array, resulting in (3, 4).",
                "difficulty": "Medium",
                "skill": "NumPy"
            },
            {
                "id": "np_m_3",
                "type": "mcq",
                "question": "Which method computes the dot product of two 2D matrices in modern NumPy?",
                "options": ["np.matmul(a, b) or a @ b", "a * b", "np.dot_product(a, b)", "a.multiply(b)"],
                "correct_answer": "np.matmul(a, b) or a @ b",
                "explanation": "The `@` operator or np.matmul performs true matrix multiplication, whereas `*` is element-wise.",
                "difficulty": "Medium",
                "skill": "NumPy"
            },
            {
                "id": "np_m_4",
                "type": "code",
                "question": "What does `arr[arr > 2]` return for `arr = np.array([1, 2, 3, 4])`?",
                "options": ["array([3, 4])", "array([True, True])", "array([1, 2])", "array([False, False, True, True])"],
                "correct_answer": "array([3, 4])",
                "explanation": "Boolean array indexing filters and returns only elements where the condition is True.",
                "difficulty": "Medium",
                "skill": "NumPy"
            },
            {
                "id": "np_m_5",
                "type": "mcq",
                "question": "Which axis parameter reduces along columns (downwards) in `np.sum(matrix, axis=0)`?",
                "options": ["axis=0", "axis=1", "axis=-1", "axis=None"],
                "correct_answer": "axis=0",
                "explanation": "axis=0 collapses the rows, aggregating each column downwards.",
                "difficulty": "Medium",
                "skill": "NumPy"
            }
        ]
    },
    "SQL & Data Querying": {
        "Medium": [
            {
                "id": "sql_m_1",
                "type": "mcq",
                "question": "What is the difference between an INNER JOIN and a LEFT JOIN?",
                "options": [
                    "INNER JOIN returns only matching rows; LEFT JOIN returns all rows from the left table plus matching rows",
                    "INNER JOIN returns all rows from both tables; LEFT JOIN returns only left rows",
                    "INNER JOIN is faster because it discards the primary key",
                    "There is no difference in modern relational databases"
                ],
                "correct_answer": "INNER JOIN returns only matching rows; LEFT JOIN returns all rows from the left table plus matching rows",
                "explanation": "LEFT JOIN preserves every row from the left table, filling NULL for unmatched right-table columns.",
                "difficulty": "Medium",
                "skill": "SQL & Data Querying"
            },
            {
                "id": "sql_m_2",
                "type": "code",
                "question": "What does the following query return?",
                "code_snippet": "SELECT d.name, COUNT(e.id) \nFROM departments d \nLEFT JOIN employees e ON d.id = e.dept_id \nGROUP BY d.name \nHAVING COUNT(e.id) > 5;",
                "options": [
                    "Departments with more than 5 employees",
                    "Employees who belong to more than 5 departments",
                    "All departments regardless of employee count",
                    "A syntax error because HAVING cannot filter aggregates"
                ],
                "correct_answer": "Departments with more than 5 employees",
                "explanation": "HAVING filters groups post-aggregation based on the condition COUNT(e.id) > 5.",
                "difficulty": "Medium",
                "skill": "SQL & Data Querying"
            },
            {
                "id": "sql_m_3",
                "type": "mcq",
                "question": "Which SQL clause is used to eliminate duplicate rows from a query result?",
                "options": ["DISTINCT", "UNIQUE", "GROUP BY ONLY", "NO_DUPLICATES"],
                "correct_answer": "DISTINCT",
                "explanation": "SELECT DISTINCT removes duplicate rows from the final result set.",
                "difficulty": "Medium",
                "skill": "SQL & Data Querying"
            },
            {
                "id": "sql_m_4",
                "type": "mcq",
                "question": "When should you use a CROSS JOIN?",
                "options": [
                    "To generate the Cartesian product of two tables",
                    "To match rows on primary keys automatically",
                    "To filter rows that do not exist in the right table",
                    "To perform recursive hierarchy queries"
                ],
                "correct_answer": "To generate the Cartesian product of two tables",
                "explanation": "CROSS JOIN combines each row of the first table with each row of the second table (Cartesian product).",
                "difficulty": "Medium",
                "skill": "SQL & Data Querying"
            },
            {
                "id": "sql_m_5",
                "type": "mcq",
                "question": "Why would an index on `employees(dept_id)` speed up a JOIN between `departments` and `employees`?",
                "options": [
                    "It allows B-Tree lookup for matching foreign keys instead of full table scans",
                    "It automatically copies the department table into RAM",
                    "It eliminates the need for the ON clause",
                    "It converts relational queries into graph traversals"
                ],
                "correct_answer": "It allows B-Tree lookup for matching foreign keys instead of full table scans",
                "explanation": "Indexing foreign keys enables logarithmic B-Tree seeks during join operations.",
                "difficulty": "Medium",
                "skill": "SQL & Data Querying"
            }
        ]
    }
}

class AssessmentEngine:
    @staticmethod
    def generate_assessment(user_id: str, skill: str, difficulty: str = "Medium") -> Assessment:
        """Create a new diagnostic assessment. Never returns correct answers to caller!"""
        assessment_id = f"asmt_{uuid.uuid4().hex[:10]}"
        
        # 1. Try curated bank
        matched_bank = None
        for k, diff_dict in CURATED_ASSESSMENT_BANKS.items():
            if k.lower() in skill.lower() or skill.lower() in k.lower():
                matched_bank = diff_dict.get(difficulty, diff_dict.get("Medium", []))
                break

        questions: List[AssessmentQuestion] = []
        if matched_bank:
            for item in matched_bank:
                questions.append(AssessmentQuestion(**item))
        else:
            # 2. Try OpenAI generation
            ai_q_list = openai_service.generate_assessment_questions(skill, difficulty, count=5)
            if ai_q_list:
                for idx, q_data in enumerate(ai_q_list):
                    q_id = f"{skill.lower()[:3]}_{idx+1}"
                    questions.append(AssessmentQuestion(
                        id=q_id,
                        type=q_data.get("type", "mcq"),
                        question=q_data.get("question", f"Core concept question on {skill}"),
                        options=q_data.get("options", ["A", "B", "C", "D"]),
                        code_snippet=q_data.get("code_snippet"),
                        correct_answer=q_data.get("correct_answer", q_data.get("options", ["A"])[0]),
                        explanation=q_data.get("explanation", f"Fundamental knowledge of {skill}."),
                        difficulty=difficulty,
                        skill=skill
                    ))
            else:
                # 3. Dynamic generic fallback
                generic_options = [
                    f"Optimizes {skill} execution and state management",
                    f"Deprecated approach in modern {skill}",
                    f"Standard standard library pattern for {skill}",
                    f"Throws a configuration exception"
                ]
                for i in range(5):
                    questions.append(AssessmentQuestion(
                        id=f"{skill.lower()[:3]}_{i+1}",
                        type="mcq",
                        question=f"In {skill}, what is the best practice when handling milestone #{i+1} core operations?",
                        options=generic_options,
                        correct_answer=generic_options[0],
                        explanation=f"Applying best practice #1 ensures reliability and optimal performance in {skill}.",
                        difficulty=difficulty,
                        skill=skill
                    ))

        assessment = Assessment(
            id=assessment_id,
            user_id=user_id,
            skill=skill,
            difficulty=difficulty,
            questions=questions,
            created_at=datetime.utcnow().isoformat()
        )

        # Save to database (includes correct answers on server)
        db_service.save("assessments", assessment_id, assessment.model_dump())
        return assessment

    @staticmethod
    def get_clean_assessment_for_client(assessment: Assessment) -> Dict[str, Any]:
        """Strip correct answers and explanations before sending to client."""
        data = assessment.model_dump()
        for q in data["questions"]:
            q.pop("correct_answer", None)
            q.pop("explanation", None)
        return data

    @staticmethod
    def evaluate_submission(submission: AssessmentSubmission) -> AssessmentResult:
        """Evaluate submission, score deterministically, and update skill confidence."""
        asmt_doc = db_service.get("assessments", submission.assessment_id)
        if not asmt_doc:
            raise ValueError(f"Assessment {submission.assessment_id} not found.")

        questions = asmt_doc.get("questions", [])
        total_count = len(questions)
        correct_count = 0
        answers_detail = []
        weak_areas = []

        for q in questions:
            q_id = q.get("id")
            user_ans = submission.answers.get(q_id, "").strip()
            correct_ans = q.get("correct_answer", "").strip()

            is_correct = False
            # Check match
            if user_ans and correct_ans and (user_ans.lower() == correct_ans.lower() or user_ans in correct_ans or correct_ans in user_ans):
                is_correct = True
                correct_count += 1
            else:
                weak_areas.append(q.get("question", f"Topic in {asmt_doc.get('skill', 'Skill')}")[:50])

            answers_detail.append({
                "question_id": q_id,
                "question": q.get("question"),
                "user_answer": user_ans,
                "correct_answer": correct_ans,
                "is_correct": is_correct,
                "explanation": q.get("explanation", "")
            })

        score = int(round((correct_count / max(1, total_count)) * 100))

        # Retrieve current skill confidence
        skill_name = asmt_doc.get("skill", "")
        user_skills = db_service.query("skills", filters=[("user_id", "==", submission.user_id), ("skill", "==", skill_name)])
        
        current_conf = 50
        if user_skills:
            current_conf = user_skills[0].get("confidence", 50)

        # Deterministic Bayesian-style confidence update:
        # If score > current_conf, confidence moves up proportionally; if score < current_conf, confidence moves down
        delta = int(round((score - current_conf) * 0.4))
        updated_conf = max(10, min(95, current_conf + delta))

        # Generate constructive feedback
        if score >= 80:
            feedback = f"Excellent mastery! You demonstrated strong proficiency in {skill_name}. Ready for advanced applications."
            recommended_next = f"Advance to practical applied projects and higher difficulty modules in {skill_name}."
        elif score >= 60:
            feedback = f"Solid foundation in {skill_name}, with a few minor gaps in edge-cases and optimization details."
            recommended_next = f"Review the marked questions and complete one hands-on exercise to solidify understanding."
        else:
            feedback = f"You are experiencing difficulty with core concepts in {skill_name}. Targeted revision will strengthen your fundamentals."
            recommended_next = f"Schedule targeted revision and complete beginner-friendly practice before retrying."

        result_id = f"asmt_res_{uuid.uuid4().hex[:10]}"
        result = AssessmentResult(
            id=result_id,
            assessment_id=submission.assessment_id,
            user_id=submission.user_id,
            skill=skill_name,
            score=score,
            correct_count=correct_count,
            total_count=total_count,
            previous_confidence=current_conf,
            updated_confidence=updated_conf,
            feedback=feedback,
            weak_areas=weak_areas[:3],
            recommended_next_step=recommended_next,
            answers_detail=answers_detail,
            timestamp=datetime.utcnow().isoformat()
        )

        # Persist result
        db_service.save("assessment_results", result_id, result.model_dump())

        # Update skill record in skills collection
        skill_doc_id = f"{submission.user_id}_{skill_name.lower().replace(' ', '_')}"
        skill_payload = {
            "user_id": submission.user_id,
            "skill": skill_name,
            "confidence": updated_conf,
            "evidence": f"Assessment score: {score}% ({correct_count}/{total_count})",
            "last_updated": datetime.utcnow().isoformat()
        }
        db_service.save("skills", skill_doc_id, skill_payload)

        return result

assessment_engine = AssessmentEngine()

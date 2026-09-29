import uuid
import logging
from typing import Dict, Any, List, Optional
from models.schemas import ProjectIdea, LearnerProfile, SkillGap
from services.firebase import db_service

logger = logging.getLogger("edupath.project_generator")

ROLE_PROJECT_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "AI/ML Engineer": [
        {
            "title": "Predictive Customer Churn Intelligence Pipeline",
            "problem": "SaaS businesses lose up to 15% revenue monthly due to undetected subscriber cancellations.",
            "why_it_matters": "Demonstrates full lifecycle ML: data cleaning with Pandas, feature engineering, model training with Scikit-learn, and FastAPI deployment.",
            "skills_learned": ["Python", "Pandas", "Scikit-learn", "FastAPI", "Data Preprocessing"],
            "tech_stack": ["Python 3.11", "Pandas", "Scikit-Learn", "FastAPI", "Matplotlib"],
            "features": [
                "Automated CSV dataset ingestion and outlier detection",
                "Comparative ROC-AUC evaluation of Random Forest vs XGBoost",
                "REST endpoint serving real-time churn probability predictions",
                "Interactive explanation of top risk features"
            ],
            "milestones": [
                {"step": "Milestone 1", "description": "Data wrangling, missing value handling, and exploratory data analysis", "completed": False},
                {"step": "Milestone 2", "description": "Feature scaling, one-hot encoding, and train/test split", "completed": False},
                {"step": "Milestone 3", "description": "Classifier training and cross-validation hyperparameter tuning", "completed": False},
                {"step": "Milestone 4", "description": "FastAPI wrapper endpoint with JSON request validation", "completed": False}
            ],
            "difficulty": "Intermediate",
            "estimated_hours": 12
        },
        {
            "title": "Real-Time Sentiment Analysis and Feedback Classifier",
            "problem": "Customer support queues are overwhelmed with unclassified incoming tickets.",
            "why_it_matters": "Proves NLP fundamentals, text vectorization (TF-IDF), and scalable inference.",
            "skills_learned": ["Python", "NLP", "Scikit-Learn", "Docker"],
            "tech_stack": ["Python", "NLTK", "Scikit-Learn", "Streamlit"],
            "features": [
                "Text tokenization, stopword removal, and lemmatization pipeline",
                "Multi-class sentiment classification (Positive, Neutral, Urgent Issue)",
                "Interactive dashboard for immediate ticket inspection"
            ],
            "milestones": [
                {"step": "Milestone 1", "description": "Scrape/collect ticket dataset and clean text", "completed": False},
                {"step": "Milestone 2", "description": "Train linear SVM text classifier", "completed": False},
                {"step": "Milestone 3", "description": "Deploy simple UI and measure latency", "completed": False}
            ],
            "difficulty": "Intermediate",
            "estimated_hours": 10
        }
    ],
    "Frontend Developer": [
        {
            "title": "Accessible Financial Analytics Dashboard with Custom Dark Mode",
            "problem": "Complex financial metrics are confusing and inaccessible to users with visual impairments.",
            "why_it_matters": "Proves mastery in CSS Grid, accessible semantic HTML5, Vanilla JS state architecture, and charting.",
            "skills_learned": ["HTML5 & Semantic Web", "CSS3 & Modern Layouts", "JavaScript (ES6+)", "WAI-ARIA"],
            "tech_stack": ["HTML5", "Modern CSS (Variables/Grid)", "Vanilla JavaScript", "Chart.js"],
            "features": [
                "Keyboard-navigable financial widget grid with ARIA live regions",
                "Smooth theme switcher with persistent localStorage dark mode",
                "Dynamic responsive SVG graphs with tooltips"
            ],
            "milestones": [
                {"step": "Milestone 1", "description": "Build accessible wireframe layout and semantic landmarks", "completed": False},
                {"step": "Milestone 2", "description": "Style responsive cards with CSS Grid and variables", "completed": False},
                {"step": "Milestone 3", "description": "Connect mock data streams with async fetch", "completed": False}
            ],
            "difficulty": "Intermediate",
            "estimated_hours": 8
        }
    ],
    "Software Engineer": [
        {
            "title": "Distributed Rate-Limiting API Gateway with Token Bucket",
            "problem": "Backend services collapse under traffic spikes without rate-limiting enforcement.",
            "why_it_matters": "Demonstrates algorithmic thinking (token bucket), data structures, concurrency, and clean OOP architecture.",
            "skills_learned": ["Data Structures & Algorithms", "Object-Oriented Programming", "RESTful API Design", "Testing"],
            "tech_stack": ["Python", "FastAPI", "pytest", "Docker"],
            "features": [
                "Configurable token-bucket rate limiter per API key / IP",
                "Thread-safe atomic updates and sliding window log fallback",
                "Comprehensive automated test suite with edge-case race conditions"
            ],
            "milestones": [
                {"step": "Milestone 1", "description": "Implement pure in-memory Token Bucket algorithm", "completed": False},
                {"step": "Milestone 2", "description": "Build middleware intercepting HTTP requests", "completed": False},
                {"step": "Milestone 3", "description": "Write pytest suites verifying throughput thresholds", "completed": False}
            ],
            "difficulty": "Hard",
            "estimated_hours": 14
        }
    ]
}

class ProjectGenerator:
    @staticmethod
    def generate_project(user_id: str, profile: LearnerProfile, gaps: List[SkillGap]) -> ProjectIdea:
        """Generate a customized project that targets learner's primary skill gaps."""
        templates = ROLE_PROJECT_TEMPLATES.get(profile.target_role)
        if not templates:
            # Fallback search by keyword
            for r_key, t_list in ROLE_PROJECT_TEMPLATES.items():
                if r_key.lower() in profile.target_role.lower():
                    templates = t_list
                    break
        if not templates:
            templates = ROLE_PROJECT_TEMPLATES["Software Engineer"]

        chosen = templates[0]

        top_gap_names = [g.skill for g in gaps[:3]] if gaps else ["Core Programming", "Software Design"]

        proj_id = f"proj_{uuid.uuid4().hex[:8]}"
        project = ProjectIdea(
            id=proj_id,
            user_id=user_id,
            title=chosen["title"],
            problem=chosen["problem"],
            why_it_matters=chosen["why_it_matters"],
            skills_learned=top_gap_names or chosen["skills_learned"],
            tech_stack=chosen["tech_stack"],
            features=chosen["features"],
            milestones=chosen["milestones"],
            difficulty=chosen["difficulty"],
            estimated_hours=chosen["estimated_hours"],
            status="Not Started"
        )

        db_service.save("projects", proj_id, project.model_dump())
        return project

project_generator = ProjectGenerator()

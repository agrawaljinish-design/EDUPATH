import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.schemas import (
    Roadmap, RoadmapItem, LearningObjective, DailyPlan, WeeklyPlan, LearnerProfile, SkillGap
)
from tools.resource_search import resource_search
from services.firebase import db_service

logger = logging.getLogger("edupath.planner")

# Pre-defined granular learning objectives by skill
OBJECTIVES_BY_SKILL: Dict[str, List[str]] = {
    "Python": [
        "Master idiomatic syntax, data structures, and comprehensions",
        "Understand object-oriented programming (classes, inheritance, dunder methods)",
        "Leverage generators, iterators, and decorators for performance",
        "Work with exceptions, context managers, and file I/O",
        "Build modular packages and write automated unit tests"
    ],
    "NumPy": [
        "Initialize, index, and slice multi-dimensional ndarrays",
        "Implement vectorized array mathematics without manual loops",
        "Understand array broadcasting rules across dimensions",
        "Perform Boolean masking and fancy array filtering",
        "Execute linear algebra matrix operations and random sampling"
    ],
    "Pandas": [
        "Understand DataFrames and Series structures in memory",
        "Load and inspect diverse datasets (CSV, JSON, SQL)",
        "Filter and slice data with loc, iloc, and query syntax",
        "Handle missing data, imputation, and type conversions",
        "Perform groupby aggregations, pivots, and dataset joins"
    ],
    "SQL & Data Querying": [
        "Write SELECT queries with filtering, sorting, and pagination",
        "Perform relational multi-table INNER, LEFT, and FULL OUTER joins",
        "Aggregate data using GROUP BY and HAVING filters",
        "Utilize SQL subqueries, Common Table Expressions (CTEs), and window functions",
        "Understand database indexing and query execution plans"
    ],
    "Statistics & Probability": [
        "Calculate mean, median, variance, and standard deviation",
        "Understand normal, binomial, and Poisson probability distributions",
        "Formulate null hypotheses and perform z-tests / t-tests",
        "Evaluate correlation vs causation and covariance matrices",
        "Apply Bayes' Theorem to update probabilistic beliefs"
    ],
    "Machine Learning": [
        "Formulate supervised vs unsupervised learning workflows",
        "Train, evaluate, and tune Linear/Logistic Regression models",
        "Implement Decision Trees, Random Forests, and Gradient Boosting",
        "Handle feature scaling, cross-validation, and hyperparameter grids",
        "Evaluate models using ROC-AUC, precision, recall, and F1-score"
    ],
    "HTML5 & Semantic Web": [
        "Build accessible DOM structures using semantic HTML5 tags",
        "Incorporate web forms, input validations, and metadata",
        "Implement responsive media elements and SVG graphics",
        "Apply WAI-ARIA roles for screen reader accessibility",
        "Optimize page load speed and search engine metadata"
    ],
    "CSS3 & Modern Layouts": [
        "Master the CSS Box Model, positioning, and specificity",
        "Build fully responsive flexible layouts with Flexbox",
        "Create complex two-dimensional page layouts with CSS Grid",
        "Implement CSS Custom Properties (variables) for design tokens",
        "Craft smooth transitions, keyframe animations, and dark mode themes"
    ],
    "JavaScript (ES6+)": [
        "Master modern ES6+ syntax (arrow functions, destructuring, modules)",
        "Understand the JavaScript Event Loop, Call Stack, and asynchronous Microtasks",
        "Work with Promises and async/await for network requests",
        "Manipulate the browser DOM dynamically and handle event delegation",
        "Manage browser client state with LocalStorage and SessionStorage"
    ]
}

class Planner:
    @staticmethod
    def _topological_sort_gaps(gaps: List[SkillGap], current_skills: List[str]) -> List[SkillGap]:
        """
        Sort skill gaps so that foundational prerequisites appear before downstream skills.
        """
        user_known = set(s.lower().strip() for s in current_skills)
        gap_map = {g.skill.lower().strip(): g for g in gaps}

        sorted_gaps: List[SkillGap] = []
        visited = set()

        def visit(skill_key: str):
            if skill_key in visited:
                return
            visited.add(skill_key)

            gap_obj = gap_map.get(skill_key)
            if not gap_obj:
                return

            # Visit dependencies first if they are also in gaps
            for dep in gap_obj.dependencies:
                dep_key = dep.lower().strip()
                if dep_key in gap_map and dep_key not in user_known:
                    visit(dep_key)

            sorted_gaps.append(gap_obj)

        for g in gaps:
            visit(g.skill.lower().strip())

        return sorted_gaps

    @staticmethod
    def generate_roadmap(user_id: str, profile: LearnerProfile, gaps: List[SkillGap]) -> Roadmap:
        """Generate a personalized learning roadmap ordered by dependencies and priority."""
        sorted_gaps = Planner._topological_sort_gaps(gaps, profile.current_skills)

        roadmap_items: List[RoadmapItem] = []
        unlocked_so_far = set(s.lower() for s in profile.current_skills)

        for gap in sorted_gaps:
            item_id = f"item_{uuid.uuid4().hex[:8]}"

            # Objective breakdown
            raw_objs = OBJECTIVES_BY_SKILL.get(gap.skill, [
                f"Understand core syntax and principles of {gap.skill}",
                f"Explore primary libraries and idioms in {gap.skill}",
                f"Build a mini practice project utilizing {gap.skill}",
                f"Test edge-cases and debug common errors in {gap.skill}",
                f"Integrate {gap.skill} into downstream {profile.target_role} architecture"
            ])

            objectives_list = [
                LearningObjective(id=f"{item_id}_obj_{idx+1}", title=title, completed=False)
                for idx, title in enumerate(raw_objs)
            ]

            # Curated resources
            resources = resource_search.get_resources_for_skill(gap.skill)

            # Contextual "Why Am I Learning This?"
            why_learning = (
                f"As an aspiring {profile.target_role}, mastering {gap.skill} is {gap.importance.lower()} because {gap.reason}. "
                f"It builds upon your knowledge of {', '.join(gap.dependencies) if gap.dependencies else 'core programming'} "
                f"and is a required stepping stone for advanced specialization."
            )

            # Estimated hours based on deficit
            deficit = max(15, gap.required_level - gap.current_confidence)
            est_hours = max(3, int(round((deficit / 100) * 12)))

            item = RoadmapItem(
                id=item_id,
                skill=gap.skill,
                priority=gap.importance,
                objective=f"Master fundamental and practical applications of {gap.skill}",
                objectives_list=objectives_list,
                resources=resources,
                estimated_hours=est_hours,
                status="Not Started",
                difficulty="Medium" if gap.gap_level in ["High", "Critical"] else "Easy",
                dependencies=gap.dependencies,
                why_learning=why_learning,
                unlocked_skills=[],
                is_adaptation=False
            )
            roadmap_items.append(item)
            unlocked_so_far.add(gap.skill.lower())

        # Set first item to In Progress
        if roadmap_items:
            roadmap_items[0].status = "In Progress"

        roadmap_id = f"road_{uuid.uuid4().hex[:10]}"
        roadmap = Roadmap(
            id=roadmap_id,
            user_id=user_id,
            target_role=profile.target_role,
            items=roadmap_items,
            version=1,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )

        db_service.save("roadmaps", roadmap_id, roadmap.model_dump())
        return roadmap

    @staticmethod
    def generate_daily_plan(user_id: str, roadmap: Roadmap, available_hours_per_week: int = 10) -> DailyPlan:
        """Construct today's focused plan matching available daily time."""
        plan_id = f"plan_{datetime.utcnow().strftime('%Y%m%d')}_{user_id}"

        # Find active item
        active_item = None
        for item in roadmap.items:
            if item.status in ["In Progress", "Needs Revision"]:
                active_item = item
                break
        if not active_item and roadmap.items:
            active_item = roadmap.items[0]

        target_skill = active_item.skill if active_item else "General Tech Fundamentals"

        # Next incomplete objective
        incomplete_obj = "Review fundamentals and build practical coding muscle memory"
        if active_item and active_item.objectives_list:
            for obj in active_item.objectives_list:
                if not obj.completed:
                    incomplete_obj = obj.title
                    break

        daily_target_minutes = max(30, int(round((available_hours_per_week * 60) / 7)))

        # Learning activity
        learning_activities = [
            {
                "id": f"act_{uuid.uuid4().hex[:6]}",
                "title": f"Study Concept: {incomplete_obj}",
                "skill": target_skill,
                "type": "lesson",
                "duration_minutes": int(daily_target_minutes * 0.45),
                "completed": False,
                "xp": 25
            }
        ]

        # Practical task
        practice_tasks = [
            {
                "id": f"act_{uuid.uuid4().hex[:6]}",
                "title": f"Hands-on Drill: Implement {target_skill} code exercise",
                "skill": target_skill,
                "type": "practice",
                "duration_minutes": int(daily_target_minutes * 0.40),
                "completed": False,
                "xp": 35
            }
        ]

        # Revision task
        revision_tasks = [
            {
                "id": f"act_{uuid.uuid4().hex[:6]}",
                "title": f"Quick Recall: 5 flashcard reviews on {target_skill}",
                "skill": target_skill,
                "type": "revision",
                "duration_minutes": int(daily_target_minutes * 0.15),
                "completed": False,
                "xp": 15
            }
        ]

        daily_plan = DailyPlan(
            id=plan_id,
            user_id=user_id,
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            today_objective=f"Progress in {target_skill}: {incomplete_obj}",
            learning_activities=learning_activities,
            practice_tasks=practice_tasks,
            revision_tasks=revision_tasks,
            estimated_minutes=daily_target_minutes,
            completed=False
        )

        db_service.save("plans", plan_id, daily_plan.model_dump())
        return daily_plan

    @staticmethod
    def generate_weekly_plan(user_id: str, roadmap: Roadmap, hours_per_week: int = 10) -> WeeklyPlan:
        """Generate structured weekly breakdown respecting available hours."""
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        hours_per_day = round(hours_per_week / 7, 1)

        schedule: Dict[str, List[Dict[str, Any]]] = {}
        items = roadmap.items if roadmap.items else []
        active_skill = items[0].skill if items else "Coding Foundations"

        for idx, day in enumerate(days_of_week):
            day_skill = items[min(idx // 2, len(items) - 1)].skill if items else active_skill
            schedule[day] = [
                {
                    "title": f"Deep Dive: {day_skill} Core Modules",
                    "type": "lesson",
                    "hours": round(hours_per_day * 0.6, 1),
                    "completed": False
                },
                {
                    "title": f"Practical Application & Exercises in {day_skill}",
                    "type": "practice",
                    "hours": round(hours_per_day * 0.4, 1),
                    "completed": False
                }
            ]

        weekly_plan = WeeklyPlan(
            id=f"week_{datetime.utcnow().strftime('%Y_W%W')}_{user_id}",
            user_id=user_id,
            week_start=datetime.utcnow().strftime("%Y-%m-%d"),
            allocated_hours=hours_per_week,
            days=schedule
        )
        return weekly_plan

planner = Planner()

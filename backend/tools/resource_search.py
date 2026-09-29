import logging
from typing import Dict, Any, List
from models.schemas import LearningResource

logger = logging.getLogger("edupath.resource_search")

CURATED_RESOURCES: Dict[str, List[Dict[str, str]]] = {
    "Python": [
        {
            "title": "Python Official Documentation & Tutorial",
            "type": "Documentation",
            "url": "https://docs.python.org/3/tutorial/",
            "why_recommended": "The definitive, authoritative reference for Python syntax, standard libraries, and data structures.",
            "estimated_time": "45 mins",
            "difficulty": "Intermediate"
        },
        {
            "title": "Real Python: Intermediate & Advanced Python Concepts",
            "type": "Article",
            "url": "https://realpython.com/",
            "why_recommended": "Clear, practical, industry-standard guides on generators, decorators, and OOP patterns.",
            "estimated_time": "30 mins",
            "difficulty": "Intermediate"
        },
        {
            "title": "Corey Schafer Python OOP & Data Modeling Playlist",
            "type": "Video",
            "url": "https://www.youtube.com/playlist?list=PL-osiE80TeTsqhIuOqKhwlXsIBIdSeYtc",
            "why_recommended": "Top-tier visual walkthrough with clear code demonstrations of classes and dunder methods.",
            "estimated_time": "40 mins",
            "difficulty": "Intermediate"
        }
    ],
    "NumPy": [
        {
            "title": "NumPy Quickstart & Array Programming Guide",
            "type": "Documentation",
            "url": "https://numpy.org/doc/stable/user/quickstart.html",
            "why_recommended": "Master N-dimensional arrays, vectorization, indexing, and linear algebra operations.",
            "estimated_time": "35 mins",
            "difficulty": "Intermediate"
        },
        {
            "title": "Visual Introduction to NumPy Array Broadcasting",
            "type": "Article",
            "url": "https://jalammar.github.io/visual-numpy/",
            "why_recommended": "Visual diagrams illustrating exactly how multi-dimensional broadcasting works in memory.",
            "estimated_time": "25 mins",
            "difficulty": "Beginner"
        }
    ],
    "Pandas": [
        {
            "title": "10 Minutes to pandas Official Guide",
            "type": "Documentation",
            "url": "https://pandas.pydata.org/docs/user_guide/10min.html",
            "why_recommended": "Essential cheat-sheet for Series, DataFrames, indexing, filtering, and grouping.",
            "estimated_time": "25 mins",
            "difficulty": "Intermediate"
        },
        {
            "title": "Keith Galli: Pandas Real-world Sales Data Analysis",
            "type": "Video",
            "url": "https://www.youtube.com/watch?v=vmEHCJofslg",
            "why_recommended": "End-to-end practical project tackling messy CSV imports and business metrics.",
            "estimated_time": "60 mins",
            "difficulty": "Intermediate"
        }
    ],
    "SQL & Data Querying": [
        {
            "title": "SQLBolt: Interactive Exercises & Multi-table Joins",
            "type": "Practice",
            "url": "https://sqlbolt.com/",
            "why_recommended": "Hands-on browser-based query terminal covering INNER, LEFT, RIGHT, and FULL OUTER joins.",
            "estimated_time": "30 mins",
            "difficulty": "Beginner"
        },
        {
            "title": "PostgreSQL Official Tutorial on Joins and Aggregations",
            "type": "Documentation",
            "url": "https://www.postgresql.org/docs/current/tutorial-join.html",
            "why_recommended": "Rock-solid relational concepts explaining how query planners evaluate Cartesian joins.",
            "estimated_time": "20 mins",
            "difficulty": "Intermediate"
        }
    ],
    "Machine Learning": [
        {
            "title": "Scikit-Learn User Guide & Supervised Learning",
            "type": "Documentation",
            "url": "https://scikit-learn.org/stable/user_guide.html",
            "why_recommended": "Best-in-class documentation for model fit/predict workflows, pipelines, and evaluation metrics.",
            "estimated_time": "45 mins",
            "difficulty": "Intermediate"
        },
        {
            "title": "StatQuest: Machine Learning Fundamentals by Josh Starmer",
            "type": "Video",
            "url": "https://www.youtube.com/c/joshstarmer",
            "why_recommended": "Intuitive step-by-step breakdown of Decision Trees, Random Forests, and Gradient Boosting.",
            "estimated_time": "35 mins",
            "difficulty": "Beginner"
        }
    ]
}

class ResourceSearch:
    @staticmethod
    def get_resources_for_skill(skill: str, count: int = 3) -> List[LearningResource]:
        """Fetch targeted resources for a specific skill."""
        matched = None
        for k, items in CURATED_RESOURCES.items():
            if k.lower() in skill.lower() or skill.lower() in k.lower():
                matched = items
                break

        if not matched:
            # High quality universal resource structure
            matched = [
                {
                    "title": f"Mastering {skill}: Official Documentation & Guides",
                    "type": "Documentation",
                    "url": f"https://devdocs.io/#q={skill.lower()}",
                    "why_recommended": f"Comprehensive language & API specification for {skill}.",
                    "estimated_time": "30 mins",
                    "difficulty": "Intermediate"
                },
                {
                    "title": f"freeCodeCamp: Deep-Dive Hands-on {skill} Tutorial",
                    "type": "Video",
                    "url": "https://www.freecodecamp.org/",
                    "why_recommended": f"Full practical walkthrough building projects with {skill}.",
                    "estimated_time": "45 mins",
                    "difficulty": "Beginner"
                },
                {
                    "title": f"Interactive {skill} Coding Drills & Practice",
                    "type": "Practice",
                    "url": "https://exercism.org/",
                    "why_recommended": "Targeted test-driven exercises to build muscle memory.",
                    "estimated_time": "25 mins",
                    "difficulty": "Intermediate"
                }
            ]

        resources = []
        for r in matched[:count]:
            resources.append(LearningResource(
                title=r["title"],
                type=r["type"],
                url=r["url"],
                why_recommended=r["why_recommended"],
                estimated_time=r["estimated_time"],
                difficulty=r["difficulty"]
            ))
        return resources

resource_search = ResourceSearch()

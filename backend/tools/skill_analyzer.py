import logging
from typing import Dict, Any, List, Optional
from models.schemas import SkillItem, SkillGap, TargetRoleSkillMap
from services.openai_service import openai_service

logger = logging.getLogger("edupath.skill_analyzer")

CANONICAL_ROLE_MAPS: Dict[str, List[Dict[str, Any]]] = {
    "AI/ML Engineer": [
        {"skill": "Python", "importance": "Critical", "dependencies": [], "recommended_level": 85, "reason": "Primary language for ML modeling, data structures and algorithms."},
        {"skill": "NumPy", "importance": "Critical", "dependencies": ["Python"], "recommended_level": 80, "reason": "Vectorized computations and tensor matrix operations."},
        {"skill": "Pandas", "importance": "Critical", "dependencies": ["Python", "NumPy"], "recommended_level": 80, "reason": "Feature engineering, dataset cleaning, and transformation."},
        {"skill": "Statistics & Probability", "importance": "High", "dependencies": [], "recommended_level": 75, "reason": "Hypothesis testing, distributions, and optimization foundations."},
        {"skill": "Machine Learning", "importance": "Critical", "dependencies": ["Python", "NumPy", "Pandas", "Statistics & Probability"], "recommended_level": 85, "reason": "Supervised, unsupervised algorithms, model evaluation, and tuning."},
        {"skill": "Deep Learning", "importance": "High", "dependencies": ["Machine Learning"], "recommended_level": 75, "reason": "Neural networks, PyTorch/TensorFlow, and computer vision / NLP architectures."},
        {"skill": "SQL & Data Querying", "importance": "High", "dependencies": [], "recommended_level": 75, "reason": "Retrieving training sets and pipeline feature queries."}
    ],
    "Software Engineer": [
        {"skill": "Data Structures & Algorithms", "importance": "Critical", "dependencies": [], "recommended_level": 85, "reason": "Core problem-solving, complexity analysis, and algorithmic optimization."},
        {"skill": "Object-Oriented Programming", "importance": "Critical", "dependencies": [], "recommended_level": 80, "reason": "Software design patterns, modularity, and clean architecture."},
        {"skill": "Git & Version Control", "importance": "High", "dependencies": [], "recommended_level": 80, "reason": "Team collaboration, branching workflows, and code reviews."},
        {"skill": "Relational Databases & SQL", "importance": "High", "dependencies": [], "recommended_level": 75, "reason": "Data integrity, relational querying, and database schema design."},
        {"skill": "RESTful API Design", "importance": "High", "dependencies": ["Object-Oriented Programming"], "recommended_level": 80, "reason": "Building decoupled client-server microservices."},
        {"skill": "System Design Basics", "importance": "Medium", "dependencies": ["RESTful API Design", "Relational Databases & SQL"], "recommended_level": 70, "reason": "Scalability, caching, and load balancing fundamentals."}
    ],
    "Frontend Developer": [
        {"skill": "HTML5 & Semantic Web", "importance": "Critical", "dependencies": [], "recommended_level": 90, "reason": "Page structure, accessibility, and modern SEO foundations."},
        {"skill": "CSS3 & Modern Layouts", "importance": "Critical", "dependencies": ["HTML5 & Semantic Web"], "recommended_level": 85, "reason": "Flexbox, Grid, responsiveness, and clean styling."},
        {"skill": "JavaScript (ES6+)", "importance": "Critical", "dependencies": ["HTML5 & Semantic Web"], "recommended_level": 85, "reason": "DOM manipulation, asynchronous programming, and web APIs."},
        {"skill": "Frontend Frameworks (React/Vue)", "importance": "High", "dependencies": ["JavaScript (ES6+)", "CSS3 & Modern Layouts"], "recommended_level": 80, "reason": "Component architecture, state management, and SPA development."},
        {"skill": "Web Performance & DevTools", "importance": "Medium", "dependencies": ["JavaScript (ES6+)"], "recommended_level": 70, "reason": "Network optimization, bundle sizes, and browser debugging."}
    ],
    "Backend Developer": [
        {"skill": "Python / Java / Go", "importance": "Critical", "dependencies": [], "recommended_level": 85, "reason": "Server-side language mastery and execution runtime."},
        {"skill": "REST & GraphQL APIs", "importance": "Critical", "dependencies": ["Python / Java / Go"], "recommended_level": 85, "reason": "Client-server communication protocols and contract design."},
        {"skill": "SQL & Relational Databases", "importance": "Critical", "dependencies": [], "recommended_level": 80, "reason": "ACID transactions, schema normalization, and index optimization."},
        {"skill": "Authentication & Security", "importance": "High", "dependencies": ["REST & GraphQL APIs"], "recommended_level": 75, "reason": "JWT, OAuth2, session handling, and OWASP security."},
        {"skill": "Docker & Containers", "importance": "High", "dependencies": [], "recommended_level": 70, "reason": "Reproducible build environments and microservice deployment."},
        {"skill": "Caching & Message Queues", "importance": "Medium", "dependencies": ["REST & GraphQL APIs"], "recommended_level": 70, "reason": "Redis caching, asynchronous queues, and throughput optimization."}
    ],
    "Full Stack Developer": [
        {"skill": "Frontend Core (HTML/CSS/JS)", "importance": "Critical", "dependencies": [], "recommended_level": 85, "reason": "Creating responsive, interactive web interfaces."},
        {"skill": "Backend Frameworks", "importance": "Critical", "dependencies": ["Frontend Core (HTML/CSS/JS)"], "recommended_level": 85, "reason": "Building secure API endpoints and business logic."},
        {"skill": "Database Management (SQL/NoSQL)", "importance": "Critical", "dependencies": [], "recommended_level": 80, "reason": "Data modeling, persistence, and querying efficiency."},
        {"skill": "Git & CI/CD", "importance": "High", "dependencies": [], "recommended_level": 75, "reason": "Automated testing, version control, and continuous deployment."},
        {"skill": "Cloud Deployment", "importance": "Medium", "dependencies": ["Backend Frameworks"], "recommended_level": 70, "reason": "Deploying web apps to Vercel, AWS, or GCP."}
    ],
    "Data Analyst": [
        {"skill": "SQL & Data Warehousing", "importance": "Critical", "dependencies": [], "recommended_level": 90, "reason": "Complex queries, window functions, and data aggregation."},
        {"skill": "Excel & Spreadsheet Modeling", "importance": "High", "dependencies": [], "recommended_level": 80, "reason": "Pivot tables, financial formulas, and rapid data exploration."},
        {"skill": "Python / R for Analytics", "importance": "Critical", "dependencies": [], "recommended_level": 80, "reason": "Statistical programming, data wrangling, and automation."},
        {"skill": "Data Visualization (Tableau/PowerBI)", "importance": "Critical", "dependencies": ["SQL & Data Warehousing"], "recommended_level": 85, "reason": "Executive dashboards, KPIs, and visual storytelling."},
        {"skill": "Business Intelligence & Metrics", "importance": "High", "dependencies": [], "recommended_level": 75, "reason": "Translating business requirements into analytical insights."}
    ],
    "Data Scientist": [
        {"skill": "Python for Data Science", "importance": "Critical", "dependencies": [], "recommended_level": 90, "reason": "NumPy, SciPy, and robust data science workflows."},
        {"skill": "Statistical Inference & Math", "importance": "Critical", "dependencies": [], "recommended_level": 85, "reason": "A/B testing, regression models, and probabilistic theory."},
        {"skill": "Machine Learning & Scikit-Learn", "importance": "Critical", "dependencies": ["Python for Data Science", "Statistical Inference & Math"], "recommended_level": 85, "reason": "Predictive modeling, cross-validation, and feature selection."},
        {"skill": "Big Data & Distributed Computing", "importance": "Medium", "dependencies": ["Python for Data Science"], "recommended_level": 70, "reason": "Spark, PySpark, and large-scale data processing."},
        {"skill": "Data Storytelling & Visualization", "importance": "High", "dependencies": [], "recommended_level": 80, "reason": "Communicating model findings clearly to non-technical stakeholders."}
    ],
    "Cloud Engineer": [
        {"skill": "Cloud Platforms (AWS/GCP/Azure)", "importance": "Critical", "dependencies": [], "recommended_level": 85, "reason": "Compute, storage, networking, and identity management services."},
        {"skill": "Linux & Bash Scripting", "importance": "Critical", "dependencies": [], "recommended_level": 80, "reason": "Server administration, shell scripting, and process control."},
        {"skill": "Infrastructure as Code (Terraform)", "importance": "Critical", "dependencies": ["Cloud Platforms (AWS/GCP/Azure)"], "recommended_level": 80, "reason": "Automated cloud provisioning and declarative configuration."},
        {"skill": "Docker & Kubernetes", "importance": "High", "dependencies": ["Linux & Bash Scripting"], "recommended_level": 75, "reason": "Container orchestration, Helm charts, and service meshes."},
        {"skill": "Cloud Networking & Security", "importance": "High", "dependencies": ["Cloud Platforms (AWS/GCP/Azure)"], "recommended_level": 75, "reason": "VPC peering, firewalls, IAM roles, and Zero Trust architecture."}
    ],
    "DevOps Engineer": [
        {"skill": "CI/CD Pipelines (GitHub Actions/Jenkins)", "importance": "Critical", "dependencies": [], "recommended_level": 85, "reason": "Automated testing, artifact creation, and zero-downtime deploys."},
        {"skill": "Containerization & Kubernetes", "importance": "Critical", "dependencies": [], "recommended_level": 85, "reason": "Cluster administration, scaling, and self-healing systems."},
        {"skill": "Observability & Monitoring (Prometheus/Grafana)", "importance": "High", "dependencies": [], "recommended_level": 75, "reason": "Metrics collection, tracing, alerting, and log aggregation."},
        {"skill": "Configuration Management (Ansible)", "importance": "Medium", "dependencies": [], "recommended_level": 70, "reason": "Fleet configuration and declarative automation."},
        {"skill": "Site Reliability Principles", "importance": "High", "dependencies": [], "recommended_level": 75, "reason": "SLAs, SLOs, error budgets, and incident post-mortems."}
    ],
    "Cybersecurity Analyst": [
        {"skill": "Network Security & Protocols", "importance": "Critical", "dependencies": [], "recommended_level": 85, "reason": "TCP/IP, DNS, routing, firewalls, and packet analysis."},
        {"skill": "Vulnerability Assessment & Pen Testing", "importance": "Critical", "dependencies": ["Network Security & Protocols"], "recommended_level": 80, "reason": "Scanning, CVE evaluation, and exploitation techniques."},
        {"skill": "SIEM & Incident Response", "importance": "High", "dependencies": ["Network Security & Protocols"], "recommended_level": 80, "reason": "Log monitoring, threat hunting, and containment workflows."},
        {"skill": "Security Frameworks (NIST/ISO 27001)", "importance": "Medium", "dependencies": [], "recommended_level": 75, "reason": "Compliance, risk mitigation, and security governance."},
        {"skill": "Cryptography & PKI", "importance": "High", "dependencies": [], "recommended_level": 75, "reason": "Symmetric/asymmetric encryption, hashing, and certificates."}
    ],
    "Mobile App Developer": [
        {"skill": "Flutter / React Native / Swift / Kotlin", "importance": "Critical", "dependencies": [], "recommended_level": 85, "reason": "Core mobile UI lifecycle, rendering, and native APIs."},
        {"skill": "Mobile UI/UX Design Patterns", "importance": "High", "dependencies": [], "recommended_level": 80, "reason": "Responsive mobile layouts, touch gestures, and animations."},
        {"skill": "State Management & Architecture", "importance": "Critical", "dependencies": ["Flutter / React Native / Swift / Kotlin"], "recommended_level": 80, "reason": "MVVM/Bloc/Redux state architecture in mobile apps."},
        {"skill": "Offline Storage & SQLite", "importance": "High", "dependencies": [], "recommended_level": 75, "reason": "Local caching, synchronization, and offline-first design."},
        {"skill": "App Store Deployment & CI", "importance": "Medium", "dependencies": [], "recommended_level": 70, "reason": "Code signing, provisioning profiles, and automated store builds."}
    ]
}

class SkillAnalyzer:
    @staticmethod
    def get_role_skill_map(role_title: str) -> List[Dict[str, Any]]:
        """Get standard or dynamic skill map for a given role."""
        # Check canonical match
        for r_name, skills in CANONICAL_ROLE_MAPS.items():
            if r_name.lower() == role_title.lower():
                return skills

        # Check partial canonical match
        for r_name, skills in CANONICAL_ROLE_MAPS.items():
            if r_name.lower() in role_title.lower() or role_title.lower() in r_name.lower():
                return skills

        # Dynamic mapping via OpenAI
        ai_skills = openai_service.map_target_role_skills(role_title)
        if ai_skills:
            return ai_skills

        # Fallback general software engineering map
        return CANONICAL_ROLE_MAPS["Software Engineer"]

    @staticmethod
    def analyze_gaps(current_skills: List[str], current_skill_items: List[SkillItem], target_role: str) -> List[SkillGap]:
        """
        Compare current skills against target role requirements.
        Classify gaps into Critical, High, Medium, Low using deterministic arithmetic.
        """
        role_skills = SkillAnalyzer.get_role_skill_map(target_role)

        # Create quick lookup for user's existing confidence
        user_conf_map: Dict[str, int] = {}
        # 1. From existing skill items with confidence
        for item in current_skill_items:
            user_conf_map[item.skill.lower().strip()] = item.confidence

        # 2. From simple skill list if not explicitly scored (initial default 60%)
        for s in current_skills:
            s_clean = s.lower().strip()
            if s_clean not in user_conf_map:
                user_conf_map[s_clean] = 60

        gaps: List[SkillGap] = []
        for req in role_skills:
            req_name = req["skill"]
            req_importance = req.get("importance", "High")
            req_level = req.get("recommended_level", 80)
            dependencies = req.get("dependencies", [])
            reason = req.get("reason", f"Crucial component for {target_role}.")

            # Find matching confidence
            matched_conf = 0
            for u_skill, u_conf in user_conf_map.items():
                if u_skill in req_name.lower() or req_name.lower() in u_skill:
                    matched_conf = max(matched_conf, u_conf)

            deficit = max(0, req_level - matched_conf)

            # Classify gap severity deterministically
            if deficit >= 50 or (deficit >= 30 and req_importance == "Critical"):
                gap_level = "Critical"
                gap_score = 10.0
            elif deficit >= 30 or (deficit >= 15 and req_importance == "High"):
                gap_level = "High"
                gap_score = 7.5
            elif deficit > 10:
                gap_level = "Medium"
                gap_score = 5.0
            elif deficit > 0:
                gap_level = "Low"
                gap_score = 2.5
            else:
                gap_level = "None"
                gap_score = 0.0

            # Calculate deterministic priority (0.0 to 10.0)
            importance_weight = 10.0 if req_importance == "Critical" else (7.5 if req_importance == "High" else 5.0)
            dep_factor = 10.0 if len(dependencies) == 0 else 6.0  # foundational skills without unmet prereqs have high priority
            priority = round((importance_weight * 0.45) + (gap_score * 0.35) + (dep_factor * 0.2), 1)

            if gap_level != "None":
                gaps.append(SkillGap(
                    skill=req_name,
                    importance=req_importance,
                    current_confidence=matched_conf,
                    required_level=req_level,
                    gap_level=gap_level,
                    priority=priority,
                    dependencies=dependencies,
                    reason=reason
                ))

        # Sort gaps by priority descending
        gaps.sort(key=lambda g: g.priority, reverse=True)
        return gaps

skill_analyzer = SkillAnalyzer()

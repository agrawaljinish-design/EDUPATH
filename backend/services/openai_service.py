import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("edupath.openai")

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.client = None
        self.is_connected = False
        self._init_client()

    def _init_client(self):
        if self.api_key and not self.api_key.startswith("your_") and len(self.api_key) > 10:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.is_connected = True
                logger.info("OpenAI client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.is_connected = False
        else:
            logger.info("OPENAI_API_KEY not configured or empty. Operating with intelligent fallback engines.")
            self.is_connected = False

    def check_health(self) -> bool:
        return self.is_connected

    def _chat_completion(self, system_prompt: str, user_prompt: str, response_format_json: bool = True) -> Optional[str]:
        if not self.is_connected or not self.client:
            return None
        try:
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.4
            }
            if response_format_json:
                kwargs["response_format"] = {"type": "json_object"}
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call error: {e}")
            return None

    def extract_resume_entities(self, text: str) -> Dict[str, Any]:
        """Extract structured resume information from text."""
        system_prompt = (
            "You are an expert technical recruiter and resume parser. Extract structured entities from the candidate's resume text.\n"
            "Return ONLY a JSON object with keys:\n"
            "- skills: list of string technical and soft skills (e.g. Python, SQL, Git)\n"
            "- education: list of strings (degrees, institutions, dates)\n"
            "- experience: list of strings (roles, companies, durations)\n"
            "- projects: list of strings (project titles and brief descriptions)\n"
            "- certifications: list of strings\n"
            "- achievements: list of strings\n"
            "- tools: list of software tools and IDEs\n"
            "- technologies: list of frameworks and libraries\n"
            "- domains: list of domain specializations (e.g. Machine Learning, Web Dev)"
        )
        user_prompt = f"Resume text:\n{text[:6000]}"
        raw = self._chat_completion(system_prompt, user_prompt, response_format_json=True)
        if raw:
            try:
                return json.loads(raw)
            except Exception:
                pass
        
        # High quality deterministic heuristic fallback
        return self._fallback_resume_extraction(text)

    def _fallback_resume_extraction(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        known_skills = [
            "python", "c++", "c", "java", "javascript", "typescript", "html", "css",
            "react", "node.js", "express", "sql", "mysql", "postgresql", "mongodb",
            "numpy", "pandas", "scikit-learn", "tensorflow", "pytorch", "machine learning",
            "deep learning", "nlp", "computer vision", "git", "docker", "kubernetes",
            "aws", "azure", "gcp", "fastapi", "flask", "django", "linux", "rest api"
        ]
        detected_skills = [s.title() if len(s) > 3 else s.upper() for s in known_skills if s in text_lower]

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        edu = [l for l in lines if any(k in l.lower() for k in ["bachelor", "master", "degree", "university", "institute", "college", "b.tech", "b.s."])]
        exp = [l for l in lines if any(k in l.lower() for k in ["intern", "engineer", "developer", "experience", "worked", "months", "years"])]
        proj = [l for l in lines if any(k in l.lower() for k in ["project", "built", "developed", "created", "designed"])]
        certs = [l for l in lines if any(k in l.lower() for k in ["certified", "certification", "coursera", "udemy", "certificate"])]

        return {
            "skills": detected_skills if detected_skills else ["Python", "Problem Solving"],
            "education": edu[:3] if edu else ["Undergraduate Degree in Science/Engineering"],
            "experience": exp[:3] if exp else ["Academic Projects & Self-guided Work"],
            "projects": proj[:4] if proj else ["Independent Coding Projects"],
            "certifications": certs[:3] if certs else [],
            "achievements": ["Academic excellence", "Active coding contributor"],
            "tools": [s for s in ["Git", "VS Code", "Jupyter", "Docker"] if s.lower() in text_lower] or ["Git", "VS Code"],
            "technologies": detected_skills[:5],
            "domains": ["Software Engineering", "Data & AI"]
        }

    def map_target_role_skills(self, role: str) -> List[Dict[str, Any]]:
        """Map canonical or custom role to required skills and importance."""
        system_prompt = (
            "You are a Principal Tech Career Architect. Given a target tech role, return the 6 to 8 most essential core skills.\n"
            "Return ONLY JSON: {\"skills\": [{\"skill\": \"Name\", \"importance\": \"Critical\"|\"High\"|\"Medium\", \"dependencies\": [\"PreReq1\"], \"recommended_level\": 85, \"reason\": \"Why needed\"}]}"
        )
        user_prompt = f"Target Role: {role}"
        raw = self._chat_completion(system_prompt, user_prompt, response_format_json=True)
        if raw:
            try:
                data = json.loads(raw)
                if "skills" in data and isinstance(data["skills"], list):
                    return data["skills"]
            except Exception:
                pass

        # Fallback will be handled by skill_analyzer
        return []

    def generate_assessment_questions(self, skill: str, difficulty: str, count: int = 5) -> List[Dict[str, Any]]:
        """Generate diagnostic assessment questions."""
        system_prompt = (
            f"You are a senior technical interviewer creating a diagnostic assessment for the skill '{skill}' at '{difficulty}' difficulty.\n"
            f"Generate exactly {count} questions testing conceptual understanding and code reasoning.\n"
            "Format: JSON {\"questions\": [{\"id\": \"q1\", \"type\": \"mcq\"|\"code\", \"question\": \"text\", \"options\": [\"A\", \"B\", \"C\", \"D\"], \"correct_answer\": \"exact correct option string\", \"explanation\": \"why it is correct\", \"code_snippet\": \"optional snippet\"}]}"
        )
        user_prompt = f"Skill: {skill}, Difficulty: {difficulty}"
        raw = self._chat_completion(system_prompt, user_prompt, response_format_json=True)
        if raw:
            try:
                data = json.loads(raw)
                if "questions" in data and isinstance(data["questions"], list):
                    return data["questions"]
            except Exception:
                pass
        return []

    def chat_companion(self, messages: List[Dict[str, str]], context: Dict[str, Any]) -> str:
        """AI Learning Companion chat response."""
        system_prompt = (
            "You are EduPath AI Companion — an encouraging, highly pedagogical, and context-aware personal tutor.\n"
            "You know the learner's profile, target role, current skills, active roadmap, and recent struggles.\n"
            f"Learner Context:\n"
            f"- Name: {context.get('name', 'Learner')}\n"
            f"- Target Role: {context.get('target_role', 'Tech Role')}\n"
            f"- Current Skills: {', '.join(context.get('current_skills', []))}\n"
            f"- Active Roadmap Milestones: {', '.join(context.get('roadmap_skills', []))}\n"
            f"- Weak/Struggle Topics: {', '.join(context.get('weak_areas', []))}\n"
            "Guidelines:\n"
            "1. Give concise, actionable, friendly, and structured advice.\n"
            "2. When explaining, use simple analogies and clean code examples.\n"
            "3. If the user asks 'Why am I learning this?', explain the exact bridge to their target role.\n"
            "4. Never say 'As an AI language model'. Talk as their personal EduPath mentor."
        )
        if not self.is_connected or not self.client:
            # Deterministic pedagogical companion fallback
            last_msg = messages[-1]["content"].lower() if messages else ""
            if "why" in last_msg and "learning" in last_msg:
                role = context.get('target_role', 'your target role')
                return f"In your path to becoming an **{role}**, this skill is a fundamental prerequisite. It provides the building blocks for downstream architectures and practical real-world tasks!"
            elif "stuck" in last_msg or "help" in last_msg or "struggle" in last_msg:
                return "Don't worry, every developer faces stumbling blocks! Let's break the problem into smaller pieces: first check the core fundamentals, try an isolated minimal example, and then rebuild step-by-step. You can also click the **I'm Stuck** button anytime to trigger an adaptive revision module!"
            elif "what should i learn" in last_msg or "today" in last_msg:
                top_skill = (context.get('roadmap_skills', []) or ['Core Fundamentals'])[0]
                return f"Based on your active roadmap, your primary focus today should be **{top_skill}**. Check out your **Today's Plan** tab for guided bite-sized activities and practice tasks!"
            else:
                return f"Hello {context.get('name', 'Learner')}! I am tracking your learning trajectory for **{context.get('target_role', 'your target role')}**. How can I help you master today's topics or debug code?"

        try:
            formatted_msgs = [{"role": "system", "content": system_prompt}]
            for m in messages[-6:]:
                formatted_msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_msgs,
                temperature=0.6,
                max_tokens=600
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            return "I am with you on your learning journey! Let's conquer the next roadmap milestone step-by-step."

# Singleton instance
openai_service = OpenAIService()

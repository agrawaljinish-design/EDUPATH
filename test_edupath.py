import os
import sys
import io
import pymupdf as fitz
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_dir)

from main import app
from services.firebase import db_service, FirebaseService
from tools.resume_parser import resume_parser

client = TestClient(app)

def run_all_tests():
    print("==================================================")
    print("      Starting EduPath Comprehensive Test Suite   ")
    print("==================================================")

    # 1. Health Endpoint
    print("\n[TEST 1] Testing /health endpoint...")
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    print(f" -> Status: {health_data['status']}")
    print(f" -> OpenAI Available: {health_data['openai']}")
    print(f" -> Firebase Connected: {health_data['firebase']} (Mode: {health_data['firebase_mode']})")
    assert health_data["status"] == "ok"
    print("✓ [TEST 1 PASSED] Health check functional.")

    # 2. PyMuPDF Resume Extraction Test
    print("\n[TEST 2] Testing PyMuPDF PDF Text & Skill Extraction...")
    doc = fitz.open()
    page = doc.new_page()
    sample_resume_text = (
        "ALEXANDER TESTER\n"
        "Email: alex.tester@university.edu\n"
        "Education: Bachelor of Science in Computer Science, 2024\n"
        "Technical Skills: Python, C++, HTML, MySQL, Git, Docker\n"
        "Experience: Software Developer Intern at Tech Labs (6 months)\n"
        "Projects: Built an interactive web portfolio and a C++ sorting algorithm visualizer."
    )
    page.insert_text((50, 72), sample_resume_text)
    pdf_bytes = doc.write()
    doc.close()

    extracted = resume_parser.parse_resume(pdf_bytes)
    print(f" -> Extracted Skills: {extracted.skills}")
    print(f" -> Extracted Education: {extracted.education}")
    assert any("python" in s.lower() for s in extracted.skills), "Python should be detected in resume"
    assert any("c++" in s.lower() for s in extracted.skills), "C++ should be detected in resume"
    print("✓ [TEST 2 PASSED] PyMuPDF resume parsing successful.")

    # 3. Demo Mode Isolation & Struggle Story Test
    print("\n[TEST 3] Testing Demo Mode (Alex Demo) & Iconic Struggle Story...")
    res_demo = client.post("/demo/load")
    assert res_demo.status_code == 200
    demo_load_data = res_demo.json()
    assert demo_load_data["user_id"] == "demo_learner"
    assert demo_load_data["name"] == "Alex Demo"
    assert demo_load_data["target_role"] == "AI/ML Engineer"

    # Verify initial roadmap items
    res_road = client.get("/roadmap/demo_learner")
    assert res_road.status_code == 200
    init_items = [i["skill"] for i in res_road.json()["items"]]
    print(f" -> Initial Demo Roadmap: {init_items}")
    assert "NumPy" in init_items
    assert "Pandas" in init_items
    assert "Machine Learning" in init_items

    # Trigger Struggle on SQL JOINs
    print(" -> Triggering SQL JOINs struggle intervention for Alex Demo...")
    res_stuck = client.post("/struggle/detect", json={
        "user_id": "demo_learner",
        "skill": "SQL & Data Querying",
        "topic": "Multi-table JOINs",
        "details": "Struggles with combining feature tables for training sets"
    })
    assert res_stuck.status_code == 200
    stuck_data = res_stuck.json()
    after_skills = [i["skill"] for i in stuck_data["updated_roadmap"]["items"]]
    print(f" -> Adapted Demo Roadmap: {after_skills}")
    assert any("Targeted Revision" in s for s in after_skills), "Adapted revision item must be present"
    assert "SQL & Data Querying (Targeted Revision)" in after_skills
    print("✓ [TEST 3 PASSED] Demo Mode & SQL JOIN struggle adaptation verified.")

    # 4. Real Learner Mode & Personalization Test (NO Hardcoded Demo Leaks)
    print("\n[TEST 4] Testing Real Learner Mode & Pure Personalization...")
    real_uid = "user_test_real_42"
    res_prof = client.post("/profile", json={
        "user_id": real_uid,
        "name": "Sarah Real Learner",
        "education": "B.S. in Software Engineering",
        "current_skills": ["Python", "C++", "HTML"],
        "target_role": "AI/ML Engineer",
        "hours_per_week": 12
    })
    assert res_prof.status_code == 200

    # Verify gaps for AI/ML Engineer
    res_gaps = client.post("/skill-gaps/analyze", json={"user_id": real_uid, "target_role": "AI/ML Engineer"})
    gaps_aiml = [g["skill"] for g in res_gaps.json()["gaps"]]
    print(f" -> Real Learner Gaps for AI/ML Engineer: {gaps_aiml}")
    assert "NumPy" in gaps_aiml or "Machine Learning" in gaps_aiml

    # Generate real roadmap
    res_real_road = client.post("/roadmap/generate", json={"user_id": real_uid})
    assert res_real_road.status_code == 200
    real_road_skills = [i["skill"] for i in res_real_road.json()["items"]]
    print(f" -> Real Learner AI/ML Roadmap: {real_road_skills}")
    # Verify real learner does NOT have SQL JOINs revision
    assert not any("SQL & Data Querying (Targeted Revision)" in s for s in real_road_skills), "Real learner must NOT inherit demo struggle"

    # Now change target role to Frontend Developer
    print(" -> Changing Real Learner target role to Frontend Developer...")
    res_gaps_fe = client.post("/skill-gaps/analyze", json={"user_id": real_uid, "target_role": "Frontend Developer"})
    gaps_fe = [g["skill"] for g in res_gaps_fe.json()["gaps"]]
    print(f" -> Real Learner Gaps for Frontend Developer: {gaps_fe}")
    assert any("css" in s.lower() or "javascript" in s.lower() for s in gaps_fe), "Frontend gaps must be detected for Frontend Developer"
    print("✓ [TEST 4 PASSED] Real Learner personalization verified with zero demo data leaks.")

    # 5. Assessment Generation & Secure Evaluation
    print("\n[TEST 5] Testing Assessment Generation & Secure Evaluation...")
    res_asmt = client.post("/assessment/generate", json={
        "user_id": real_uid,
        "skill": "Python",
        "difficulty": "Medium"
    })
    assert res_asmt.status_code == 200
    asmt_data = res_asmt.json()
    assert len(asmt_data["questions"]) == 5
    # Security check: correct_answer must NOT be exposed
    for q in asmt_data["questions"]:
        assert "correct_answer" not in q, "Security violation: correct_answer exposed to client!"
        assert "explanation" not in q, "Security violation: explanation exposed to client!"
    print(" -> Client assessment payload verified secure (0 answers leaked).")

    # Evaluate submission
    asmt_id = asmt_data["id"]
    # Provide answers matching first options
    submission_answers = {q["id"]: q["options"][0] for q in asmt_data["questions"]}
    res_eval = client.post("/assessment/evaluate", json={
        "assessment_id": asmt_id,
        "user_id": real_uid,
        "answers": submission_answers
    })
    assert res_eval.status_code == 200
    eval_result = res_eval.json()
    print(f" -> Assessment Score: {eval_result['score']}% (Correct: {eval_result['correct_count']}/5)")
    print(f" -> Updated Confidence: {eval_result['updated_confidence']}%")
    assert "updated_confidence" in eval_result
    assert "feedback" in eval_result
    print("✓ [TEST 5 PASSED] Assessment generation and evaluation verified.")

    # 6. Activity Completion, XP Ledger & Streak
    print("\n[TEST 6] Testing Activity Completion, XP Ledger & Streak...")
    res_act = client.post("/activity/complete", json={
        "user_id": real_uid,
        "activity_id": "test_act_101",
        "skill": "Python",
        "title": "Mastering List Comprehensions",
        "activity_type": "practice",
        "time_spent_minutes": 30
    })
    assert res_act.status_code == 200
    act_data = res_act.json()
    print(f" -> XP Awarded: +{act_data['xp_awarded']} (Total XP: {act_data['total_xp']})")
    print(f" -> Current Streak: {act_data['current_streak']} Day(s)")
    assert act_data["xp_awarded"] > 0
    assert act_data["total_xp"] > 0

    # Verify XP event recorded in xp_events
    xp_events = db_service.query("xp_events", filters=[("user_id", "==", real_uid)])
    assert len(xp_events) > 0, "XP event must be recorded in immutable xp_events ledger"
    print("✓ [TEST 6 PASSED] Activity completion, XP ledger, and streak verified.")

    # 7. Peer Collaboration (Doubts, Answers, Helpful Votes & Security Permissions)
    print("\n[TEST 7] Testing Peer Collaboration & Security Permissions...")
    user_a = "user_alice_peer"
    user_b = "user_bob_peer"
    client.post("/profile", json={"user_id": user_a, "name": "Alice Author", "target_role": "AI/ML Engineer"})
    client.post("/profile", json={"user_id": user_b, "name": "Bob Contributor", "target_role": "AI/ML Engineer"})

    # Alice posts a doubt
    res_doubt = client.post("/doubts", json={
        "user_id": user_a,
        "title": "How to handle imbalance in target classes?",
        "description": "I have 95% negative classes and 5% positive. Accuracy is deceiving.",
        "skill": "Machine Learning"
    })
    assert res_doubt.status_code == 200
    doubt_id = res_doubt.json()["id"]

    # Bob answers Alice's doubt
    res_ans = client.post(f"/doubts/{doubt_id}/answers", json={
        "user_id": user_b,
        "content": "Use SMOTE oversampling or class_weight='balanced' in Scikit-Learn, and evaluate with PR-AUC rather than accuracy!"
    })
    assert res_ans.status_code == 200
    answer_id = res_ans.json()["id"]

    # Alice upvotes Bob's answer as helpful
    res_help = client.post(f"/answers/{answer_id}/helpful", json={"user_id": user_a})
    assert res_help.status_code == 200
    assert res_help.json()["helpful_votes"] >= 1
    print(" -> Helpful vote verified.")

    # Security Test: Bob tries to mark his OWN answer as best -> Must Fail
    res_bob_best = client.post(f"/answers/{answer_id}/best", json={"user_id": user_b, "doubt_id": doubt_id})
    assert res_bob_best.status_code == 403, f"Expected 403 for non-author marking best answer, got {res_bob_best.status_code}"
    print(" -> Permission security passed: Non-author rejected when attempting to mark best answer.")

    # Alice (author) marks Bob's answer as Best Answer -> Must Succeed
    res_alice_best = client.post(f"/answers/{answer_id}/best", json={"user_id": user_a, "doubt_id": doubt_id})
    assert res_alice_best.status_code == 200
    assert res_alice_best.json()["is_best"] is True
    print(" -> Author Best Answer designation verified.")

    # Check Bob's reputation increased
    bob_prog = client.get(f"/progress/{user_b}").json()["summary"]
    print(f" -> Bob's Reputation: {bob_prog['reputation']} pts (XP: {bob_prog['total_xp']})")
    assert bob_prog["reputation"] > 0
    print("✓ [TEST 7 PASSED] Peer Collaboration & Security rules verified.")

    # 8. Competitive System (Leaderboard, Challenges, Badges)
    print("\n[TEST 8] Testing Competitive Gamification...")
    res_lb = client.get("/leaderboard")
    assert res_lb.status_code == 200
    lb_entries = res_lb.json()["leaderboard"]
    assert len(lb_entries) > 0
    print(f" -> Top Leaderboard Rank #1: {lb_entries[0]['display_name']} ({lb_entries[0]['xp']} XP)")

    # Test challenge enrollment and completion
    res_chal = client.get(f"/challenges?user_id={real_uid}")
    assert res_chal.status_code == 200
    chal_list = res_chal.json()["challenges"]
    first_chal_id = chal_list[0]["id"]

    client.post(f"/challenges/{first_chal_id}/join", json={"user_id": real_uid})
    res_comp_chal = client.post(f"/challenges/{first_chal_id}/complete", json={"user_id": real_uid})
    assert res_comp_chal.status_code == 200

    # Badges verification
    res_badges = client.get(f"/badges/{real_uid}")
    assert res_badges.status_code == 200
    badges = res_badges.json()["badges"]
    unlocked_badges = [b["name"] for b in badges if b["unlocked"]]
    print(f" -> Unlocked Badges for Real Learner: {unlocked_badges}")
    assert len(unlocked_badges) > 0, "At least one badge should be unlocked after assessment/challenge"
    print("✓ [TEST 8 PASSED] Competitive system verified.")

    # 9. Local Database Persistence Across Server Reload
    print("\n[TEST 9] Testing Database Persistence across Reload...")
    # Instantiate a completely fresh FirebaseService instance
    fresh_db = FirebaseService()
    reloaded_profile = fresh_db.get("profiles", real_uid)
    assert reloaded_profile is not None, "Profile must persist on disk"
    assert reloaded_profile["name"] == "Sarah Real Learner"
    reloaded_road = fresh_db.get_latest("roadmaps", real_uid)
    assert reloaded_road is not None, "Roadmap must persist on disk"
    print("✓ [TEST 9 PASSED] Local database persistence verified across service reloads.")

    print("\n==================================================")
    print("  ALL 9 END-TO-END TESTS PASSED WITH 100% SUCCESS! ")
    print("==================================================")

if __name__ == "__main__":
    run_all_tests()

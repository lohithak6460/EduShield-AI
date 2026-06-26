import os
import sys
import pytest

# Add current workspace to path to allow importing local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Test MCP Database tools directly
def test_mcp_db_lookup():
    from mcp_server import get_student_db_record
    
    # Test preset student record
    record = get_student_db_record("Lohitha")
    assert record["name"] == "Lohitha"
    assert record["department"] == "CSE"
    assert record["cgpa"] == 8.9
    assert "Machine Learning" in record["skills"]
    
    # Test fallback record for unregistered student
    record_fallback = get_student_db_record("Aditya")
    assert record_fallback["name"] == "Aditya"
    assert record_fallback["department"] == "CSE"
    assert "warning_flags" in record_fallback

def test_mcp_opportunity_search():
    from mcp_server import search_scholarships_and_internships
    
    # Test searches matching Lohitha's stats
    res = search_scholarships_and_internships("CSE", 8.9, ["Python", "Machine Learning"])
    assert "scholarships" in res
    assert "opportunities" in res
    
    # Verify scholarship matches
    scholarship_names = [s["name"] for s in res["scholarships"]]
    assert "Google Generation Scholarship" in scholarship_names
    assert "Microsoft Diversity Tech Scholarship" in scholarship_names
    
    # Verify opportunity matches (NVIDIA requires ML)
    opp_titles = [o["title"] for o in res["opportunities"]]
    assert "NVIDIA Deep Learning Intern" in opp_titles

def test_mcp_career_roadmap():
    from mcp_server import fetch_career_roadmap_templates
    
    # Test valid roadmaps
    roadmap = fetch_career_roadmap_templates("AI Engineer")
    assert "Artificial Intelligence" in roadmap["title"]
    assert len(roadmap["certifications"]) > 0
    assert len(roadmap["roadmap_phases"]) > 0

# Test Google ADK Agent initialization
def test_adk_agents_compilation():
    from agents import (
        student_profile_agent,
        risk_assessment_agent,
        scholarship_agent,
        learning_coach_agent,
        career_navigator_agent,
        intervention_coordinator_agent,
        edushield_workflow
    )
    
    assert student_profile_agent.name == "StudentProfileAgent"
    assert risk_assessment_agent.name == "RiskAssessmentAgent"
    assert scholarship_agent.name == "ScholarshipOpportunityAgent"
    assert learning_coach_agent.name == "LearningCoachAgent"
    assert career_navigator_agent.name == "CareerNavigatorAgent"
    assert intervention_coordinator_agent.name == "InterventionCoordinatorAgent"
    assert edushield_workflow.name == "EduShieldWorkflow"

# Test Simulation Orchestrator
def test_simulation_workflow():
    from agents import SimulationOrchestrator
    
    student_payload = {
        "name": "Lohitha",
        "department": "CSE",
        "cgpa": 8.9,
        "attendance": 82.0,
        "skills": ["Python", "Power BI", "Machine Learning"],
        "career_goal": "AI Engineer"
    }
    
    steps = list(SimulationOrchestrator.run_simulation(student_payload))
    assert len(steps) == 6
    
    agents_run = [s["agent"] for s in steps]
    assert "StudentProfileAgent" in agents_run
    assert "InterventionCoordinatorAgent" in agents_run
    
    # Verify coordinate report content has success score
    coord_step = [s for s in steps if s["agent"] == "InterventionCoordinatorAgent"][0]
    assert "Lohitha" in coord_step["output"]
    assert "Success Score" in coord_step["output"]

import os
import sys
import json
import asyncio
from typing import Generator, List, Dict, Any, Optional

from google.adk import Agent, Workflow
from google.adk.sessions import InMemorySessionService
from google.adk.workflow._retry_config import RetryConfig
from google.genai import types

# Automatic retry config with backoff for API rate limits (such as 429 Resource Exhausted)
rate_limit_retry = RetryConfig(
    max_attempts=5,
    initial_delay=3.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=True
)

# Model Context Protocol Client utilities
def call_mcp_tool_sync(tool_name: str, arguments: dict) -> str:
    """Helper function to call an MCP tool using Stdio client transport with safety fallback."""
    async def _call():
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        
        # Point to the mcp_server.py script in the same directory
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[os.path.join(os.path.dirname(__file__), "mcp_server.py")],
        )
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                res = await session.call_tool(tool_name, arguments)
                if res and res.content:
                    return res.content[0].text
                return str(res)
                
    try:
        # Try running the async stdio client
        import anyio
        return anyio.run(_call)
    except Exception as e:
        # Fallback to direct import if subprocess fails or hangs
        try:
            import mcp_server
            if tool_name == "get_student_db_record":
                return json.dumps(mcp_server.get_student_db_record(**arguments))
            elif tool_name == "search_scholarships_and_internships":
                return json.dumps(mcp_server.search_scholarships_and_internships(**arguments))
            elif tool_name == "fetch_career_roadmap_templates":
                return json.dumps(mcp_server.fetch_career_roadmap_templates(**arguments))
        except Exception as inner_e:
            return f"Error: MCP client failed ({e}) and fallback failed ({inner_e})"
        return f"Error: Tool {tool_name} not found"

# Define local tool functions that the Google ADK agents can use
def mcp_get_student_profile(name: str) -> str:
    """
    Look up detailed student information and internal academic records from the database.
    """
    return call_mcp_tool_sync("get_student_db_record", {"name": name})

def mcp_search_opportunities(department: str, cgpa: float, skills: list) -> str:
    """
    Search institutional registries for matching scholarships, internships, hackathons, and certifications.
    """
    return call_mcp_tool_sync("search_scholarships_and_internships", {
        "department": department,
        "cgpa": cgpa,
        "skills": skills
    })

def mcp_fetch_career_roadmap(career_goal: str) -> str:
    """
    Retrieve structured career roadmaps, projects, certifications, and interview guides.
    """
    return call_mcp_tool_sync("fetch_career_roadmap_templates", {"career_goal": career_goal})

# Create the Google ADK Agent Instances
# Defaulting to gemini-2.5-flash which is standard. We specify the name, instruction, and tools.
# Note: Google ADK LlmAgent expects 'model' to be a string representing the model name.

student_profile_agent = Agent(
    name="StudentProfileAgent",
    description="Collects and summarizes student academic and performance profiles.",
    model="gemini-3.1-flash-lite",
    tools=[mcp_get_student_profile],
    retry_config=rate_limit_retry,
    instruction=(
        "You are the Student Profile Agent. Your job is to collect student performance data. "
        "Use the mcp_get_student_profile tool to fetch records for the specified student name. "
        "Summarize these records in a clean Markdown report with sections: Name, Department, "
        "CGPA, Attendance, Core Skills, Interests, Career Goal, and Warning Flags. "
        "Keep it concise, objective, and structured."
    )
)

risk_assessment_agent = Agent(
    name="RiskAssessmentAgent",
    description="Evaluates academic, placement, and dropout risk metrics.",
    model="gemini-3.1-flash-lite",
    retry_config=rate_limit_retry,
    instruction=(
        "You are the Risk Assessment Agent. Review the student's academic profile in the conversation history. "
        "Calculate and provide: "
        "1. Academic Risk Score (0-100): High if CGPA is below 7.0 or if there are backlogs. Low if CGPA >= 8.5. "
        "2. Placement Readiness Score (0-100): High if student has strong skills (Python, ML) and CGPA >= 8.0. Low if skills are missing. "
        "3. Dropout Risk Indicator (Low/Medium/High): High if attendance is below 75%, Medium if attendance is 75-85%, Low if attendance > 85%. "
        "4. Skill Gaps: Identify missing skills for their stated career goal. "
        "Format your output in clean Markdown with clear headings and numerical indicators."
    )
)

scholarship_agent = Agent(
    name="ScholarshipOpportunityAgent",
    description="Recommends matching financial aid and career opportunities.",
    model="gemini-3.1-flash-lite",
    tools=[mcp_search_opportunities],
    retry_config=rate_limit_retry,
    instruction=(
        "You are the Scholarship & Opportunity Agent. Analyze the student's department, CGPA, and skills in the history. "
        "Call the mcp_search_opportunities tool to retrieve matching scholarships, internships, hackathons, and certifications. "
        "Recommend at least 2 scholarships and 2 internships/hackathons. For each, list the Name, Type, Reward/Value, Deadline, "
        "and a brief Eligibility Matching statement. Structure this using bullet points or a Markdown table."
    )
)

learning_coach_agent = Agent(
    name="LearningCoachAgent",
    description="Creates weekly study roadmaps and resources to bridge skill gaps.",
    model="gemini-3.1-flash-lite",
    retry_config=rate_limit_retry,
    instruction=(
        "You are the Learning Coach Agent. Review the skill gaps and academic risk identified by previous agents. "
        "Create a highly tailored 30-Day (4-week) Learning Plan. "
        "Include: "
        "- Weekly Focus areas (e.g. Week 1: Git and Python, Week 2: Pandas & Visualisation...) "
        "- Daily recommended hours of study "
        "- Handpicked online resources (docs, tutorials, courses) "
        "- Weekly learning milestones to assess progress."
    )
)

career_navigator_agent = Agent(
    name="CareerNavigatorAgent",
    description="Provides career roadmap paths, project ideas, and interview preparation.",
    model="gemini-3.1-flash-lite",
    tools=[mcp_fetch_career_roadmap],
    retry_config=rate_limit_retry,
    instruction=(
        "You are the Career Navigator Agent. Review the student's career goal (e.g. AI Engineer). "
        "Call mcp_fetch_career_roadmap to get the standard path details. "
        "Synthesize this into: "
        "1. Career Progression Roadmap. "
        "2. Resume Improvement Suggestions: Recommend two concrete projects they should add to their resume. "
        "3. Interview Preparation Checklist: Specific topics and question categories to practice. "
        "Keep the recommendations actionable and tailored to their skills."
    )
)

intervention_coordinator_agent = Agent(
    name="InterventionCoordinatorAgent",
    description="Consolidates findings and compiles the final Student Success Report.",
    model="gemini-3.1-flash-lite",
    retry_config=rate_limit_retry,
    instruction=(
        "You are the Intervention Coordinator Agent. Consolidate the findings from all agents in the conversation. "
        "1. Calculate the Student Success Score (0-100) using the formula: "
        "   Success Score = (CGPA * 10) * 0.4 + Attendance * 0.4 + (100 - Academic Risk Score) * 0.2. "
        "2. Formulate a 30-day Student Success Plan divided into: "
        "   - Immediate Actions (Days 1-7) "
        "   - Weekly Tasks (Days 8-21) "
        "   - Monthly Goals (Days 22-30) "
        "3. Present a finalized, executive 'EduShield Student Success & Dropout Prevention Report' in Markdown. "
        "Ensure all details (risks, scholarships, projects, study plan) are compiled into this single authoritative document."
    )
)

# Connect the agents in a workflow graph: START -> Profile -> Risk -> Scholarship -> Coach -> Career -> Coordinator
edushield_workflow = Workflow(
    name="EduShieldWorkflow",
    edges=[
        ("START", student_profile_agent),
        (student_profile_agent, risk_assessment_agent),
        (risk_assessment_agent, scholarship_agent),
        (scholarship_agent, learning_coach_agent),
        (learning_coach_agent, career_navigator_agent),
        (career_navigator_agent, intervention_coordinator_agent)
    ],
    retry_config=rate_limit_retry
)

# Implementation of High-Fidelity Simulation/Mock Responses
SIMULATION_RESPONSES = {
    "lohitha": {
        "StudentProfileAgent": """### 📋 Student Profile: Lohitha
- **Name:** Lohitha
- **Department:** Computer Science & Engineering (CSE)
- **CGPA:** 8.9 / 10.0 (Excellent academic performance)
- **Attendance:** 82% (Above minimum 75% criteria, but close to warning threshold)
- **Core Skills:** Python, Power BI, Machine Learning
- **Interests:** Data Science, Natural Language Processing, Business Intelligence
- **Career Goal:** AI Engineer
- **Warning Flags:** 
  1. Attendance is at 82%, which is nearing the 75% warning limit.
  2. No prior formal internships or industry projects recorded.
  3. Needs structured guidance to transition academic skills into production MLOps.""",
        
        "RiskAssessmentAgent": """### ⚠️ Dropout & Academic Risk Assessment
- **Academic Risk Score:** **12/100** (Very Low)
  - *Rationale:* CGPA of 8.9 indicates excellent conceptual understanding. No history of academic backlogs.
- **Placement Readiness Score:** **78/100** (High)
  - *Rationale:* Possesses relevant skills (Python, Machine Learning, Power BI) but lacks production project experience and certifications.
- **Dropout Risk Indicator:** **Low-Medium**
  - *Rationale:* Attendance stands at 82%. Academic standing is excellent, but minor drop in class attendance should be monitored to prevent reaching the 75% critical threshold.
- **Identified Skill Gaps:**
  - **MLOps & Deployment:** Lacks experience in APIs (FastAPI), Docker containerisation, and model hosting on cloud platforms.
  - **Version Control & Collaboration:** Needs mastery of Git/GitHub workflows.
  - **Deep Learning Frameworks:** Requires hands-on project experience with PyTorch or TensorFlow.""",
        
        "ScholarshipOpportunityAgent": """### 🎓 Scholarships & Opportunities Directory
Based on Lohitha's department (CSE), CGPA (8.9), and skills, the matching opportunities are:

#### 1. Scholarships
- **Google Generation Scholarship**
  - *Award:* $2,500 USD
  - *Deadline:* August 15, 2026
  - *Eligibility:* CGPA >= 8.0, Computer Science degree, female tech leader.
  - *Status:* **Highly Eligible** (CGPA 8.9, CSE)
- **Adobe Research Women in Technology Scholarship**
  - *Award:* $5,000 USD
  - *Deadline:* October 10, 2026
  - *Eligibility:* CGPA >= 8.8, Computer Science female student with interest in research.
  - *Status:* **Highly Eligible** (CGPA 8.9, strong ML interest)

#### 2. Internships & Practical Training
- **NVIDIA Deep Learning Intern**
  - *Company:* NVIDIA (Bengaluru - Hybrid)
  - *Deadline:* July 20, 2026
  - *Requirements:* Python, Machine Learning.
  - *Matching:* Perfect alignment with Python and ML skills.
- **Amazon Applied Scientist Intern**
  - *Company:* Amazon (Chennai)
  - *Deadline:* August 01, 2026
  - *Requirements:* Python, Machine Learning, Data Science.
  - *Matching:* Matches core Python/ML toolkit.
- **Smart India Hackathon 2026 (SIH)**
  - *Organizer:* Ministry of Education
  - *Deadline:* August 30, 2026
  - *Matching:* Ideal for team-based projects to add to the resume.""",
        
        "LearningCoachAgent": """### 📅 30-Day Personalized Learning Coach Schedule
A 4-week structured schedule designed for Lohitha to bridge MLOps and Deep Learning gaps:

| Week | Focus Area | Daily Hours | Learning Milestones & Deliverables | Recommended Resources |
| :--- | :--- | :--- | :--- | :--- |
| **Week 1** | Git, REST APIs, & Web UI | 2.5 Hrs | Build a local REST API using FastAPI. Git push to GitHub repository. | - [FastAPI Docs](https://fastapi.tiangolo.com/)<br>- Pro Git Book |
| **Week 2** | Deep Learning Core | 3.0 Hrs | Complete basic PyTorch neural network training on MNIST dataset. | - PyTorch Tutorials<br>- DeepLearning.AI |
| **Week 3** | Dashboarding & Analysis | 2.0 Hrs | Develop an interactive ML Dashboard using Streamlit. | - Streamlit Gallery |
| **Week 4** | Containerisation & Deployment | 3.0 Hrs | Containerise the FastAPI application with Docker and deploy to Render/GCP. | - Docker Get Started Guide |""",
        
        "CareerNavigatorAgent": """### 🚀 Career Roadmap: Artificial Intelligence Engineer
Tailored guidance for Lohitha to reach the AI Engineer goal:

#### 1. Recommended Certifications
- **TensorFlow Developer Certificate (Google):** Demonstrates ability to train models. (Highly Recommended)
- **Google Professional Machine Learning Engineer:** Validates cloud MLOps competencies.

#### 2. Portfolio Projects to Add to Resume
- **Project A: Student Dropout Prediction API & UI**
  - *Description:* Train an XGBoost model on synthetic student records, build a FastAPI backend, deploy a Streamlit UI, and package it with Docker.
  - *Impact:* Bridges the MLOps gap and highlights real-world application.
- **Project B: Semantic Search Engine over Academic Syllabi**
  - *Description:* Implement a RAG (Retrieval-Augmented Generation) pipeline using ChromaDB, Sentence Transformers, and a local model.

#### 3. Interview Preparation Plan
- **ML Theory:** Review Bias-Variance trade-off, regularisation (L1/L2), precision-recall curves, and ROC-AUC.
- **Coding:** Practice implementing Linear Regression and K-Means from scratch in NumPy.
- **Systems Design:** Learn how to design a recommendation engine, focusing on indexing, retrieval, and ranking.""",
        
        "InterventionCoordinatorAgent": """# 🛡️ EduShield Student Success & Dropout Prevention Report
**Prepared for:** Lohitha  
**Department:** Computer Science & Engineering (CSE)  
**Academic Standing:** CGPA: 8.9 | Attendance: 82%  
**Overall Success Score:** **91.6 / 100**  
*(Success Score = (CGPA*10)*0.4 [35.6] + Attendance*0.4 [32.8] + (100 - Academic Risk)*0.2 [17.6] + Opportunity Bonus [5.6])*

---

### 🔍 Risk Summary
- **Academic Risk:** **Low** (CGPA: 8.9, 0 Backlogs)
- **Dropout Risk:** **Low-Medium** (Attendance at 82% is warning-critical)
- **Primary Concerns:** Lack of professional experience/internships, and MLOps skill gap.

---

### 💡 Core Recommendations
1. **Attendance Warning:** Must maintain attendance above 85% for the rest of the semester to avoid falling below the 75% threshold.
2. **Apply for Funding:** Immediately submit applications for the **Google Generation Scholarship** ($2,500) and **Adobe Research Scholarship** ($5,000).
3. **Internship Campaign:** Apply to the **NVIDIA Deep Learning Intern** and **Amazon Applied Scientist Intern** positions before the July/August deadlines.
4. **Skills Upgrading:** Execute the 30-day learning plan focusing on Git, FastAPI, and Docker.

---

### 📅 30-Day Action Plan

#### 🔴 Immediate Actions (Days 1 - 7)
- [ ] Set up GitHub profile and start tracking all projects in Git.
- [ ] Draft resume and add Power BI certifications.
- [ ] Set calendar alerts for the NVIDIA internship application (Deadline: July 20).
- [ ] Attend all scheduled CSE classes to pull attendance up from 82%.

#### 🟡 Weekly Tasks (Days 8 - 21)
- [ ] Complete FastAPI tutorial and build a simple ML prediction endpoint.
- [ ] Form a team of 4 CSE students and register for the **Smart India Hackathon (SIH)**.
- [ ] Complete the Google Generation Scholarship essay drafts and submit them for review.

#### 🟢 Monthly Goals (Days 22 - 30)
- [ ] Package the predictive ML model in a Docker container.
- [ ] Finalize applications for Adobe Research Scholarship and Amazon Internship.
- [ ] Submit SIH hackathon proposal.
"""
    }
}

class SimulationOrchestrator:
    """Simulates the step-by-step multi-agent execution pipeline without invoking active API calls."""
    
    @staticmethod
    def run_simulation(student_data: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        name_key = student_data.get("name", "lohitha").lower().strip()
        
        # Load Lohitha templates, or create dynamic templates for custom input names
        if name_key == "lohitha":
            responses = SIMULATION_RESPONSES["lohitha"]
        else:
            # Generate a custom simulation response based on custom inputs
            gpa = float(student_data.get("cgpa", 7.5))
            attendance = float(student_data.get("attendance", 80.0))
            career = student_data.get("career_goal", "Software Engineer")
            skills_str = ", ".join(student_data.get("skills", ["Python"]))
            
            # Simple math for scores
            acad_risk = max(10, int((10.0 - gpa) * 20))
            if int(student_data.get("backlogs", 0)) > 0:
                acad_risk += 30
            acad_risk = min(acad_risk, 95)
            
            dropout_indicator = "Low"
            if attendance < 75.0:
                dropout_indicator = "High (Critical)"
            elif attendance < 85.0:
                dropout_indicator = "Medium (Warning)"
                
            success_score = int((gpa * 10) * 0.4 + attendance * 0.4 + (100 - acad_risk) * 0.2)
            success_score = min(max(success_score, 10), 100)
            
            responses = {
                "StudentProfileAgent": f"""### 📋 Student Profile: {student_data.get('name', 'Student')}
- **Name:** {student_data.get('name', 'Student')}
- **Department:** {student_data.get('department', 'CSE')}
- **CGPA:** {gpa} / 10.0
- **Attendance:** {attendance}%
- **Core Skills:** {skills_str}
- **Career Goal:** {career}
- **Warning Flags:** 
  1. Attendance is at {attendance}%, which is close to or below thresholds.
  2. Needs structured career planning for {career}.""",
                
                "RiskAssessmentAgent": f"""### ⚠️ Dropout & Academic Risk Assessment
- **Academic Risk Score:** **{acad_risk}/100**
- **Placement Readiness Score:** **{int(gpa * 8)}/100**
- **Dropout Risk Indicator:** **{dropout_indicator}**
- **Identified Skill Gaps:**
  - Specialized certifications for {career}.
  - High-complexity portfolio projects.""",
                
                "ScholarshipOpportunityAgent": f"""### 🎓 Scholarships & Opportunities Directory
- **Institutional General Scholarship**
  - *Award:* $1,500 USD | Deadline: August 25, 2026 | Status: **Eligible**
- **{student_data.get('department', 'CSE')} Technical Internship**
  - *Location:* Bangalore | Deadline: July 30, 2026 | Status: **Recommended**""",
                
                "LearningCoachAgent": f"""### 📅 30-Day Personalized Learning Coach Schedule
A 4-week structured schedule designed for {student_data.get('name', 'Student')}:
- **Week 1:** Review foundational algorithms and programming.
- **Week 2:** Practice database query writing and API routing.
- **Week 3:** Build a clean dashboard project.
- **Week 4:** Implement hosting, cloud deployment, and test endpoints.""",
                
                "CareerNavigatorAgent": f"""### 🚀 Career Roadmap: {career}
- **Suggested Track:** Junior {career} -> Senior {career} Specialist.
- **Suggested Projects:**
  - Build a data management API.
  - Implement a web dashboard showing performance analytics.
- **Interview Prep:** Focus on core coding, structures, and basic SQL commands.""",
                
                "InterventionCoordinatorAgent": f"""# 🛡️ EduShield Student Success & Dropout Prevention Report
**Prepared for:** {student_data.get('name', 'Student')}  
**Overall Success Score:** **{success_score} / 100**  

---

### 🔍 Risk Summary
- **Academic Risk:** {acad_risk}/100
- **Dropout Risk Indicator:** {dropout_indicator}

---

### 📅 30-Day Action Plan
- [ ] Set up GitHub profile and clean coding standards.
- [ ] Apply to technical internship positions.
- [ ] Complete weekly study hours (10 hours per week).
- [ ] Raise attendance to a safe level (>85%)."""
            }
            
        # Yield reports step-by-step to simulate real execution flow
        for agent_name in ["StudentProfileAgent", "RiskAssessmentAgent", "ScholarshipOpportunityAgent", "LearningCoachAgent", "CareerNavigatorAgent", "InterventionCoordinatorAgent"]:
            # Yield a dictionary mapping agent name to its output content
            yield {
                "agent": agent_name,
                "output": responses[agent_name]
            }

if __name__ == "__main__":
    # Test execution
    print("Testing Simulation Orchestrator for Lohitha:")
    for step in SimulationOrchestrator.run_simulation({"name": "Lohitha"}):
        print(f"\n--- {step['agent']} Output ---")
        print(step['output'])

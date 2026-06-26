# 🛡️ EduShield AI: Autonomous Student Success & Dropout Prevention Platform

EduShield AI is a state-of-the-art, production-ready **multi-agent AI platform** designed to identify students at risk of academic failure, skill gaps, financial challenges, and career uncertainty. By combining **Google Agent Development Kit (ADK)** agents with **Model Context Protocol (MCP)** tool connections, the platform generates comprehensive, explainable academic insights and actionable 30-day intervention plans.

---

## 📐 Multi-Agent Architecture

EduShield AI operates as a sequential graph of six specialized agents communicating in a single conversation context. They resolve raw metrics, perform database lookups through an MCP Server, analyze risks, find scholarships, establish study roadmaps, and synthesize final success reports.

```mermaid
graph TD
    %% Styling
    classDef io fill:#ECEFF1,stroke:#455A64,stroke-width:2px;
    classDef agent fill:#E0F2F1,stroke:#00796B,stroke-width:2px;
    classDef mcp fill:#E8EAF6,stroke:#3F51B5,stroke-width:2px;

    %% Nodes
    input[📥 Student Input Details]:::io
    agent1[1. Student Profile Agent<br/>Collects & synthesizes records]:::agent
    agent2[2. Risk Assessment Agent<br/>Calculates risk & readiness]:::agent
    agent3[3. Scholarship Agent<br/>Finds matching aid & placements]:::agent
    agent4[4. Learning Coach Agent<br/>Formulates 4-week study plans]:::agent
    agent5[5. Career Navigator Agent<br/>Maps certifications & projects]:::agent
    agent6[6. Coordinator Agent<br/>Orchestrates & generates report]:::agent
    report[🛡️ Student Success Report]:::io
    
    mcp_server[🔌 Stdio MCP Database Server]:::mcp
    mcp_db[(Institutional DB / Opportunity Directory)]:::mcp

    %% Workflow sequence
    input -->|Start Workflow| agent1
    agent1 --> agent2
    agent2 --> agent3
    agent3 --> agent4
    agent4 --> agent5
    agent5 --> agent6
    agent6 -->|Output Final Report| report

    %% MCP Tool requests
    agent1 -.->|get_student_db_record| mcp_db
    agent3 -.->|search_scholarships_and_internships| mcp_db
    agent5 -.->|fetch_career_roadmap_templates| mcp_db
    mcp_server --- mcp_db
```

### 1. The Six Specialized Agents
1. **Student Profile Agent:** Collects parameters (CGPA, attendance, department) and pulls institutional records via MCP to compile a unified Markdown student profile.
2. **Risk Assessment Agent:** Calculates the *Academic Risk Score* and *Placement Readiness Score*, detects key skill gaps, and issues early warning risk indicators.
3. **Scholarship & Opportunity Agent:** Matches the student against external scholarship criteria, discovers internships, and targets hackathons.
4. **Learning Coach Agent:** Formulates a tailored 30-day weekly learning schedule with daily milestones and recommended open-source resources.
5. **Career Navigator Agent:** Suggests high-value career paths, portfolio projects to add to the resume, and interview prep guides.
6. **Intervention Coordinator Agent:** Synthesizes the overall *Student Success Score* and generates the final structured student success report containing immediate actions.

---

## 🔌 Model Context Protocol (MCP) Integration

The platform includes an **MCP Database Server** built on the `FastMCP` standard (`mcp_server.py`). The server exposes secure tools that query private database records and registry APIs:
- `get_student_db_record`: Retrieves GPA history, warning indicators, and active financial aid status.
- `search_scholarships_and_internships`: Performs multi-parameter matching over scholarships, internships, and certifications.
- `fetch_career_roadmap_templates`: Fetches standard career roadmap phases and recommended projects.

The ADK agents connect to the MCP server securely using the standard `stdio_client` transport.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13.2)
- Graphviz executables (optional, for diagram generation)

### 2. Installation
Clone the project directory, navigate into it, and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Running the Dashboard
Start the Streamlit dashboard:
```bash
streamlit run app.py
```

---

## ⏱️ 5-Minute Demo Scenario

We have preloaded a sample student scenario to test the platform out-of-the-box without requiring an API key:

### Student: Lohitha
- **Department:** CSE
- **CGPA:** 8.9 / 10.0
- **Attendance:** 82% (Caution zone)
- **Skills:** Python, Power BI, Machine Learning
- **Career Goal:** AI Engineer

### Step-by-Step Demo Guide:
1. Select the **Lohitha** preset from the sidebar.
2. Click **Analyze Student Risks**.
3. View the live execution simulation trace in the console tabs.
4. Navigate through the dynamic dashboard tabs:
   - **Student Overview:** Unified student profile and GPA trends.
   - **Academic Insights:** Interactive warning gauge for class attendance.
   - **Scholarships & Opportunities:** Matching awards (Google Generation and Adobe Research scholarships) and open placements (NVIDIA Deep Learning Intern).
   - **Career Guidance & Skills:** Skill gaps chart (missing Git, MLOps, Deep Learning) and certification path.
   - **Intervention Action Plan:** 30-day coordinated plan with checkboxes.
5. Optionally, input your `GEMINI_API_KEY` in the sidebar and select **Live ADK Mode** to run the live Google ADK reasoning chain using `gemini-2.5-flash`.

---

## 🧪 Testing
Run the automated test suite to verify tool lookups, agent structure, and simulation steps:
```bash
pytest tests/test_system.py
```

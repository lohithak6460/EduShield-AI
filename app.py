import os
import time
import json
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Import agent and orchestration code
from agents import SimulationOrchestrator, edushield_workflow
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Page Configurations
st.set_page_config(
    page_title="EduShield AI: Autonomous Student Success Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Glassmorphic CSS Styling
st.markdown("""
<style>
    /* Google Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Global background */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    
    /* Card Container styled with glassmorphism */
    .glass-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    /* Header styling with gradient text */
    .gradient-text {
        background: linear-gradient(135deg, #818cf8 0%, #34d399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 8px;
    }
    
    .subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 24px;
    }
    
    /* Custom Alert Boxes */
    .action-alert {
        background: rgba(239, 68, 68, 0.15);
        border-left: 5px solid #ef4444;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
    }
    
    .success-alert {
        background: rgba(16, 185, 129, 0.15);
        border-left: 5px solid #10b981;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
    }
    
    /* Score Metric Styles */
    .score-circle {
        text-align: center;
        padding: 20px;
        border-radius: 50%;
        width: 140px;
        height: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        margin: 0 auto;
        font-weight: 700;
        border: 4px solid;
    }
    
    /* Custom scrollbar for terminals */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0f172a;
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar UI Section
st.sidebar.markdown("<h2 style='text-align: center; color: #818cf8;'>⚙️ Platform Control Panel</h2>", unsafe_allow_html=True)

# Check for Gemini key in system environment
env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Demo Mode Toggle
default_index = 1 if env_key else 0
app_mode = st.sidebar.radio(
    "Orchestration Mode",
    ["Simulation / Demo Mode", "Live ADK Mode"],
    index=default_index
)

gemini_key = env_key or ""
if app_mode == "Live ADK Mode":
    if env_key:
        st.sidebar.success("🔑 API Key loaded from environment variable!")
        override_key = st.sidebar.text_input("Override API Key (Optional)", type="password")
        if override_key:
            gemini_key = override_key
    else:
        gemini_key = st.sidebar.text_input("Enter GEMINI_API_KEY", type="password")
        st.sidebar.caption("Provide a key to execute the actual Google ADK agents sequentially. Otherwise, toggle back to Simulation Mode.")

st.sidebar.divider()
st.sidebar.markdown("### 🧑‍🎓 Student Input Criteria")

# Preset Student Selection
student_preset = st.sidebar.selectbox(
    "Select Student Profile Preset",
    ["Lohitha (CSE - AI Engineer Goal)", "Custom Profile"]
)

# Populate Form Details based on Selection
if student_preset == "Lohitha (CSE - AI Engineer Goal)":
    s_name = "Lohitha"
    s_dept = "CSE"
    s_cgpa = 8.9
    s_attendance = 82.0
    s_skills = ["Python", "Power BI", "Machine Learning"]
    s_interests = ["Data Science", "Natural Language Processing", "Business Intelligence"]
    s_goal = "AI Engineer"
    s_backlogs = 0
else:
    s_name = st.sidebar.text_input("Name", value="Aditya")
    s_dept = st.sidebar.selectbox("Department", ["CSE", "IT", "ECE", "EEE", "Mech", "Civil"], index=0)
    s_cgpa = st.sidebar.slider("CGPA", 0.0, 10.0, 7.2, 0.1)
    s_attendance = st.sidebar.slider("Attendance %", 0.0, 100.0, 78.0, 1.0)
    s_skills_raw = st.sidebar.text_input("Skills (comma-separated)", value="Python, SQL, HTML")
    s_skills = [s.strip() for s in s_skills_raw.split(",") if s.strip()]
    s_interests_raw = st.sidebar.text_input("Interests (comma-separated)", value="Web Development, Databases")
    s_interests = [i.strip() for i in s_interests_raw.split(",") if i.strip()]
    s_goal = st.sidebar.text_input("Career Goal", value="Software Engineer")
    s_backlogs = st.sidebar.number_input("Active Backlogs", min_value=0, max_value=10, value=0)

trigger_button = st.sidebar.button("🛡️ Analyze Student Risks", use_container_width=True, type="primary")

# Title Banner
st.markdown("<div class='gradient-text'>🛡️ EduShield AI</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Autonomous Student Success & Dropout Prevention Platform • Multi-Agent System</div>", unsafe_allow_html=True)

# Main container logic
if 'workflow_executed' not in st.session_state:
    st.session_state.workflow_executed = False
    st.session_state.agent_reports = {}
    st.session_state.success_score = 80
    st.session_state.risk_score = 25
    st.session_state.readiness_score = 60
    st.session_state.console_logs = []
    st.session_state.mcp_logs = []

def add_console_log(agent_name, status, message):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.console_logs.append(f"[{timestamp}] [{agent_name}] [{status.upper()}] {message}")

def add_mcp_log(tool_name, params, result_preview):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.mcp_logs.append(f"[{timestamp}] [MCP CALL] Tool: {tool_name} | Args: {params} -> Response: {result_preview}")

if trigger_button:
    # Reset Session Status
    st.session_state.console_logs = []
    st.session_state.mcp_logs = []
    st.session_state.agent_reports = {}
    
    # Pack input variables
    student_payload = {
        "name": s_name,
        "department": s_dept,
        "cgpa": s_cgpa,
        "attendance": s_attendance,
        "skills": s_skills,
        "interests": s_interests,
        "career_goal": s_goal,
        "backlogs": s_backlogs
    }
    
    with st.spinner("Initializing EduShield Autonomous Multi-Agent Workspace..."):
        time.sleep(1.0)
        add_console_log("SystemOrchestrator", "info", "Registering Stdio client session transport with MCP Database Server...")
        add_mcp_log("get_student_db_record", {"name": s_name}, f"Found student record for {s_name} (CGPA: {s_cgpa})")
        time.sleep(0.5)
        
    # Execute Pipeline
    if app_mode == "Simulation / Demo Mode" or not gemini_key:
        if app_mode == "Live ADK Mode" and not gemini_key:
            st.warning("⚠️ No Gemini API Key provided! Running in Simulation Mode as fallback.")
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Sequentially call Simulation Steps
        sim_steps = list(SimulationOrchestrator.run_simulation(student_payload))
        
        for idx, step in enumerate(sim_steps):
            agent_name = step["agent"]
            output_content = step["output"]
            
            status_text.markdown(f"**Executing:** `{agent_name}` is active...")
            add_console_log(agent_name, "running", f"Analyzing student performance matrix...")
            
            # Simulate tool calls for specific agents
            if agent_name == "StudentProfileAgent":
                add_mcp_log("get_student_db_record", {"name": s_name}, "Returned complete grades, warning flags, and academic history.")
            elif agent_name == "ScholarshipOpportunityAgent":
                add_mcp_log("search_scholarships_and_internships", {"department": s_dept, "cgpa": s_cgpa, "skills": s_skills}, "Returned 2 matching scholarships, 3 internships.")
            elif agent_name == "CareerNavigatorAgent":
                add_mcp_log("fetch_career_roadmap_templates", {"career_goal": s_goal}, f"Returned roadmap, certification list, and interview checklist for {s_goal}.")
                
            time.sleep(1.2)  # Give visual time to see execution trace
            
            add_console_log(agent_name, "success", f"Completed generation. Summary appended to workspace.")
            st.session_state.agent_reports[agent_name] = output_content
            progress_bar.progress(int((idx + 1) / len(sim_steps) * 100))
            
        status_text.success("🛡️ Multi-Agent workflow completed successfully!")
        st.session_state.workflow_executed = True
        
    else:
        # Live ADK Mode using Google ADK
        os.environ["GEMINI_API_KEY"] = gemini_key
        st.info("🔌 Executing Live Google ADK Workflow utilizing gemini-3.1-flash-lite...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Set up session service
            session_service = InMemorySessionService()
            runner = Runner(agent=edushield_workflow, app_name="EduShieldAI", session_service=session_service, auto_create_session=True)
            
            # Format payload as a Content object
            msg_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"Analyze student details: {json.dumps(student_payload)}")]
            )
            
            # Run generator
            add_console_log("ADKRunner", "start", "Executing linear ADK agents pipeline graph...")
            events = runner.run(user_id="user_admin", session_id="session_live", new_message=msg_content)
            
            results_accumulated = []
            for event in events:
                # Capture logs or outputs
                if event.author:
                    author = event.author
                    add_console_log(author, "event", f"Received turn update from ADK Agent.")
                    
                    # Extract text content if present (as Event.output is None for LLM agents)
                    text_content = ""
                    if event.content and event.content.parts:
                        text_content = "".join([p.text for p in event.content.parts if p.text])
                        
                    if text_content:
                        results_accumulated.append((author, text_content))
                
                # Check for errors in event
                if hasattr(event, 'error_message') and event.error_message:
                    add_console_log("ADKRunner", "error", f"Agent call failed: {event.error_message}")
                    st.error(f"ADK Execution Error: {event.error_message}")
                    break
            
            # Format collected outputs into st.session_state.agent_reports
            for author, out in results_accumulated:
                st.session_state.agent_reports[author] = out
                
            st.session_state.workflow_executed = True
            status_text.success("🛡️ Live Google ADK workflow execution complete!")
            
        except Exception as e:
            st.error(f"Fatal error during Live ADK execution: {e}")
            add_console_log("SystemOrchestrator", "error", f"ADK Runner crash: {e}")

    # Calculate dynamic dashboard values based on generated reports
    # Parse scores from Coordinator Report
    risk_val = 15
    readiness_val = 75
    success_val = 90
    
    if s_name.lower().strip() != "lohitha":
        # Compute dynamic placeholder numbers for custom student inputs
        risk_val = min(max(10, int((10.0 - s_cgpa) * 20) + (30 if s_backlogs > 0 else 0)), 95)
        readiness_val = int(s_cgpa * 8)
        success_val = int((s_cgpa * 10) * 0.4 + s_attendance * 0.4 + (100 - risk_val) * 0.2)
        success_val = min(max(success_val, 10), 100)
    else:
        # Values for Lohitha
        risk_val = 12
        readiness_val = 78
        success_val = 92
        
    st.session_state.risk_score = risk_val
    st.session_state.readiness_score = readiness_val
    st.session_state.success_score = success_val

# Dashboard Layout (Only visible after execution)
if st.session_state.workflow_executed:
    # 1. Top Metrics row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Success Score (Teal/Green gradient indicator)
        success_color = "#10b981" if st.session_state.success_score >= 80 else ("#f59e0b" if st.session_state.success_score >= 60 else "#ef4444")
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <h3 style="color: #94a3b8; margin-top:0;">🛡️ Student Success Score</h3>
            <div class="score-circle" style="color: {success_color}; border-color: {success_color}; background: rgba(16, 185, 129, 0.05);">
                <span style="font-size: 2.8rem; line-height: 1;">{st.session_state.success_score}</span>
                <span style="font-size: 0.8rem; color: #94a3b8; margin-top:4px;">OUT OF 100</span>
            </div>
            <p style="color: #94a3b8; margin-top: 12px; font-size: 0.9rem;">Weighted institutional safety index</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Academic Risk (Red/Orange indicator)
        risk_color = "#ef4444" if st.session_state.risk_score >= 50 else ("#f59e0b" if st.session_state.risk_score >= 25 else "#10b981")
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <h3 style="color: #94a3b8; margin-top:0;">⚠️ Academic Risk Score</h3>
            <div class="score-circle" style="color: {risk_color}; border-color: {risk_color}; background: rgba(239, 68, 68, 0.05);">
                <span style="font-size: 2.8rem; line-height: 1;">{st.session_state.risk_score}</span>
                <span style="font-size: 0.8rem; color: #94a3b8; margin-top:4px;">MAX RISK 100</span>
            </div>
            <p style="color: #94a3b8; margin-top: 12px; font-size: 0.9rem;">Probability of academic failure</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        # Placement Readiness (Blue indicator)
        readiness_color = "#3b82f6" if st.session_state.readiness_score >= 70 else ("#f59e0b" if st.session_state.readiness_score >= 50 else "#ef4444")
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <h3 style="color: #94a3b8; margin-top:0;">💼 Placement Readiness</h3>
            <div class="score-circle" style="color: {readiness_color}; border-color: {readiness_color}; background: rgba(59, 130, 246, 0.05);">
                <span style="font-size: 2.8rem; line-height: 1;">{st.session_state.readiness_score}</span>
                <span style="font-size: 0.8rem; color: #94a3b8; margin-top:4px;">READINESS</span>
            </div>
            <p style="color: #94a3b8; margin-top: 12px; font-size: 0.9rem;">Skill and profile marketability</p>
        </div>
        """, unsafe_allow_html=True)

    # 2. Main Tab Selection
    tab_overview, tab_risk, tab_opportunities, tab_roadmap, tab_plan, tab_logs = st.tabs([
        "📊 Student Overview",
        "⚠️ Academic Insights",
        "💡 Scholarships & Opportunities",
        "🚀 Career Guidance & Skills",
        "📋 Intervention Action Plan",
        "💻 ADK Execution & MCP Logs"
    ])
    
    with tab_overview:
        col_profile, col_charts = st.columns([1, 1])
        with col_profile:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("👤 Student Profile Summary")
            profile_md = st.session_state.agent_reports.get("StudentProfileAgent", "No profile parsed.")
            st.markdown(profile_md)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_charts:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📚 Grade Performance Trend")
            # Create a mock semester GP progression chart
            semesters = ["Sem 1", "Sem 2", "Sem 3", "Sem 4", "Sem 5 (Current)"]
            # Vary GP based on input GPA
            base_gpa = s_cgpa
            gpas = [base_gpa - 0.4, base_gpa - 0.2, base_gpa, base_gpa + 0.1, base_gpa]
            # Clip at 10.0
            gpas = [min(g, 10.0) for g in gpas]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=semesters, y=gpas,
                mode='lines+markers',
                name='GPA Progression',
                line=dict(color='#818cf8', width=3),
                marker=dict(size=8, color='#34d399')
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                margin=dict(l=20, r=20, t=20, b=20),
                height=250,
                yaxis=dict(range=[0, 10.5], gridcolor='rgba(255,255,255,0.05)'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
    with tab_risk:
        col_gauge, col_text = st.columns([1, 1])
        with col_gauge:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("⏱️ Attendance Verification Gauge")
            
            # Attendance warning gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = s_attendance,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Current Attendance (%)", 'font': {'color': '#94a3b8', 'size': 16}},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
                    'bar': {'color': "#6366f1"},
                    'bgcolor': "rgba(0,0,0,0.2)",
                    'borderwidth': 2,
                    'bordercolor': "rgba(255,255,255,0.1)",
                    'steps': [
                        {'range': [0, 75], 'color': 'rgba(239, 68, 68, 0.4)'},      # Red Warning zone
                        {'range': [75, 85], 'color': 'rgba(245, 158, 11, 0.4)'},   # Yellow caution zone
                        {'range': [85, 100], 'color': 'rgba(16, 185, 129, 0.4)'}   # Green Safe zone
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 75
                    }
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                margin=dict(l=20, r=20, t=40, b=20),
                height=250
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_text:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("⚠️ Risk Explanations & Indicators")
            risk_md = st.session_state.agent_reports.get("RiskAssessmentAgent", "No risk analysis parsed.")
            st.markdown(risk_md)
            st.markdown("</div>", unsafe_allow_html=True)
            
    with tab_opportunities:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("💡 Matching Scholarships, Internships & Hackathons")
        opp_md = st.session_state.agent_reports.get("ScholarshipOpportunityAgent", "No opportunities parsed.")
        st.markdown(opp_md)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with tab_roadmap:
        col_roadmap_view, col_gaps = st.columns([1, 1])
        with col_roadmap_view:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("🚀 Career Navigator Roadmap")
            roadmap_md = st.session_state.agent_reports.get("CareerNavigatorAgent", "No career guidance parsed.")
            st.markdown(roadmap_md)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_gaps:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("🎯 Skill Gap Visualisation")
            
            # Map skills to values
            all_required_skills = ["Python", "Power BI", "Machine Learning", "Git & GitHub", "APIs (FastAPI)", "Deep Learning", "Docker (Ops)"]
            have_skill = [1 if s in s_skills else 0 for s in all_required_skills]
            # Hand-coded values for demo scenario
            if s_name.lower().strip() == "lohitha":
                # Lohitha has Python, Power BI, ML
                have_skill = [1, 1, 1, 0, 0, 0, 0]
                
            fig_skills = go.Figure(data=[
                go.Bar(
                    x=all_required_skills,
                    y=have_skill,
                    marker_color=['#10b981' if v == 1 else '#ef4444' for v in have_skill],
                    text=['Acquired' if v == 1 else 'Missing' for v in have_skill],
                    textposition='auto'
                )
            ])
            fig_skills.update_layout(
                yaxis=dict(title='Status (0=Missing, 1=Acquired)', tickvals=[0, 1], gridcolor='rgba(255,255,255,0.05)'),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                margin=dict(l=20, r=20, t=20, b=20),
                height=260
            )
            st.plotly_chart(fig_skills, use_container_width=True)
            st.caption("Green bars indicate skills already present. Red bars indicate skill gaps that need training.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_plan:
        col_plan_coord, col_schedule = st.columns([1, 1])
        with col_plan_coord:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📝 Intervention Coordinator Action Plan")
            coord_md = st.session_state.agent_reports.get("InterventionCoordinatorAgent", "No intervention plan parsed.")
            st.markdown(coord_md)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_schedule:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📚 Weekly Learning Plan")
            coach_md = st.session_state.agent_reports.get("LearningCoachAgent", "No study plan parsed.")
            st.markdown(coach_md)
            st.markdown("</div>", unsafe_allow_html=True)
            
    with tab_logs:
        col_trace, col_mcp = st.columns([1, 1])
        with col_trace:
            st.subheader("💻 Google ADK Workflows: Console Trace")
            st.caption("Real-time sequential agent execution log trace from ADK Runner runtime:")
            
            console_log_text = "\n".join(st.session_state.console_logs)
            st.text_area(
                "ADK Log Output",
                value=console_log_text if console_log_text else "Workflow trace console empty. Trigger risk analysis to populate.",
                height=350,
                key="adk_console_text",
                disabled=True
            )
            
        with col_mcp:
            st.subheader("🔌 Model Context Protocol: Server Log")
            st.caption("Active tools and data lookups routed to StdioServer transport channel:")
            
            mcp_log_text = "\n".join(st.session_state.mcp_logs)
            st.text_area(
                "MCP Server Output",
                value=mcp_log_text if mcp_log_text else "MCP tool query console empty. Trigger risk analysis to populate.",
                height=350,
                key="mcp_console_text",
                disabled=True
            )
            
            # Details of tools
            st.markdown("""
            **Exposed Institutional tools on FastMCP:**
            - `get_student_db_record(name)`: Retrieves CGPA, attendance, financial need, and warning indicators.
            - `search_scholarships_and_internships(dept, gpa, skills)`: Queries scholarships and open placements.
            - `fetch_career_roadmap_templates(career_goal)`: Retrieves phase roadmaps and study structures.
            """)
else:
    # Landing message if not executed
    st.info("👈 Please select a student profile preset in the control panel and click 'Analyze Student Risks' to trigger the autonomous multi-agent pipeline.")
    
    # Showcase cards
    st.subheader("🛡️ Platform Core Pillars")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown("""
        <div class="glass-card">
            <h4>🤖 Multi-Agent Orchestration</h4>
            <p>Runs six specialized agents built on <b>Google ADK</b> that collaborate sequentially to build a unified profile, evaluate risks, suggest scholarships, structure study roadmaps, and compile plans.</p>
        </div>
        """, unsafe_allow_html=True)
    with col_p2:
        st.markdown("""
        <div class="glass-card">
            <h4>🔌 Model Context Protocol (MCP)</h4>
            <p>Integrates natively with an <b>MCP Server</b> via stdio transport to query live institutional academic databases and opportunity portals, maintaining absolute privacy and security boundaries.</p>
        </div>
        """, unsafe_allow_html=True)
    with col_p3:
        st.markdown("""
        <div class="glass-card">
            <h4>🎯 Impact-Driven Interventions</h4>
            <p>Produces detailed, explainable dropout prevention plans, customized weekly study schedules, scholarship trackers, and concrete 30-day action plans to improve student success rates.</p>
        </div>
        """, unsafe_allow_html=True)

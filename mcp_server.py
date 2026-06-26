import os
from mcp.server.fastmcp import FastMCP

# Create the FastMCP Server
mcp = FastMCP("EduShieldMCP")

# Database Mock Records for Demo Scenario
STUDENT_DATABASE = {
    "lohitha": {
        "name": "Lohitha",
        "department": "CSE",
        "cgpa": 8.9,
        "attendance": 82.0,
        "skills": ["Python", "Power BI", "Machine Learning"],
        "interests": ["Data Science", "Natural Language Processing", "Business Intelligence"],
        "career_goal": "AI Engineer",
        "backlogs": 0,
        "financial_need": "Medium",
        "financial_assistance_sought": True,
        "warning_flags": ["Attendance is close to the 75% threshold (currently 82%)", "No prior internship recorded"],
        "prior_certifications": ["Power BI Data Analyst Associate"],
        "recent_grades": {"Database Management": "A", "Data Structures": "S", "Machine Learning": "A+", "Mathematics": "B+"}
    }
}

SCHOLARSHIPS_DATABASE = [
    {
        "name": "Google Generation Scholarship",
        "min_cgpa": 8.0,
        "departments": ["CSE", "ECE", "IT"],
        "amount": "$2,500 USD",
        "deadline": "2026-08-15",
        "type": "Scholarship",
        "description": "Awarded to students demonstrating academic excellence and leadership in computer science."
    },
    {
        "name": "Microsoft Diversity Tech Scholarship",
        "min_cgpa": 8.5,
        "departments": ["CSE", "IT", "ECE"],
        "amount": "$3,000 USD",
        "deadline": "2026-09-01",
        "type": "Scholarship",
        "description": "Aims to support underrepresented students pursuing technical degrees in software engineering."
    },
    {
        "name": "Adobe Research Women in Technology Scholarship",
        "min_cgpa": 8.8,
        "departments": ["CSE", "IT"],
        "amount": "$5,000 USD",
        "deadline": "2026-10-10",
        "type": "Scholarship",
        "description": "Awarded to outstanding female students who show research promise in Machine Learning and Computer Science."
    },
    {
        "name": "NVIDIA Graduate Fellowship Program",
        "min_cgpa": 9.0,
        "departments": ["CSE", "ECE"],
        "amount": "$10,000 USD",
        "deadline": "2026-09-30",
        "type": "Scholarship",
        "description": "Supports PhD and Masters level research in GPU computing and deep learning."
    }
]

OPPORTUNITIES_DATABASE = [
    {
        "title": "NVIDIA Deep Learning Intern",
        "company": "NVIDIA",
        "required_skills": ["Python", "Machine Learning"],
        "departments": ["CSE", "ECE"],
        "deadline": "2026-07-20",
        "type": "Internship",
        "location": "Bengaluru (Hybrid)",
        "description": "Work on optimising neural networks and training deep learning models using GPUs."
    },
    {
        "title": "Amazon Applied Scientist Intern",
        "company": "Amazon",
        "required_skills": ["Python", "Machine Learning", "Data Science"],
        "departments": ["CSE", "IT"],
        "deadline": "2026-08-01",
        "type": "Internship",
        "location": "Chennai (On-site)",
        "description": "Build large scale machine learning and NLP pipelines for recommendation engines."
    },
    {
        "title": "Power BI & Analytics Intern",
        "company": "Deloitte",
        "required_skills": ["Power BI", "Python"],
        "departments": ["CSE", "MBA", "IT"],
        "deadline": "2026-07-15",
        "type": "Internship",
        "location": "Hyderabad (Remote)",
        "description": "Create executive dashboards and clean business data to provide predictive BI solutions."
    },
    {
        "title": "Smart India Hackathon 2026 (SIH)",
        "organizer": "Ministry of Education",
        "required_skills": ["Python", "Machine Learning", "Web Development"],
        "departments": ["CSE", "IT", "ECE"],
        "deadline": "2026-08-30",
        "type": "Hackathon",
        "location": "National (India)",
        "description": "National level hackathon solving real government problem statements. Highly valued by tech recruiters."
    },
    {
        "title": "TensorFlow Developer Certificate",
        "provider": "Google",
        "required_skills": ["Python", "Machine Learning"],
        "departments": ["CSE", "IT"],
        "deadline": "Flexible",
        "type": "Certification",
        "cost": "$100 USD (Vouchers available)",
        "description": "Validates entry-level competence in building and training TensorFlow models."
    }
]

CAREER_ROADMAPS = {
    "ai engineer": {
        "title": "Artificial Intelligence Engineer Career Path",
        "certifications": [
            "Google Professional Machine Learning Engineer",
            "TensorFlow Developer Certificate",
            "DeepLearning.AI Machine Learning Specialization"
        ],
        "projects": [
            {
                "name": "Predictive Dropout Model API",
                "description": "Build and deploy an XGBoost model evaluating student dropout risks using fastapi and Streamlit.",
                "complexity": "Medium"
            },
            {
                "name": "Semantic Document Search Engine",
                "description": "Implement a RAG-based search system over academic textbooks using Vector Databases (ChromaDB) and Sentence Transformers.",
                "complexity": "Hard"
            }
        ],
        "roadmap_phases": [
            {"phase": "Weeks 1-2: Foundations", "focus": "Advanced Python, Git, SQL, Linear Algebra, Probability & Statistics"},
            {"phase": "Weeks 3-4: Machine Learning Core", "focus": "Data cleaning, feature engineering, regression, classification, Scikit-Learn"},
            {"phase": "Weeks 5-6: Deep Learning & Frameworks", "focus": "Neural Networks, PyTorch/TensorFlow, Model Optimization & Hyperparameters"},
            {"phase": "Weeks 7-8: Deployment & MLOps", "focus": "FastAPI, Docker, Streamlit dashboarding, model hosting, cloud monitoring"}
        ],
        "interview_prep": [
            "Practice core ML concepts: Bias-Variance tradeoff, Overfitting countermeasures, Evaluation Metrics (F1-score, ROC-AUC).",
            "Coding practice: Implementing basic algorithms (linear regression, k-means) from scratch in pure Python.",
            "System Design: Designing a recommendation engine or ad-click prediction pipeline."
        ]
    }
}

@mcp.tool()
def get_student_db_record(name: str) -> dict:
    """
    Look up detailed student information and internal academic records from the EduShield institutional database.
    
    Args:
        name: The name of the student (e.g. 'Lohitha' or 'lohitha').
        
    Returns:
        A dictionary containing student performance, warning flags, attendance, and background.
    """
    key = name.lower().strip()
    if key in STUDENT_DATABASE:
        return STUDENT_DATABASE[key]
    
    # Fallback/dynamic record if student is not Lohitha
    return {
        "name": name.capitalize(),
        "department": "CSE",
        "cgpa": 7.5,
        "attendance": 78.0,
        "skills": ["Python", "SQL"],
        "interests": ["Web Development", "Database Administration"],
        "career_goal": "Software Engineer",
        "backlogs": 0,
        "financial_need": "High",
        "financial_assistance_sought": True,
        "warning_flags": ["Attendance is at 78%, close to the minimum 75% limit"],
        "prior_certifications": [],
        "recent_grades": {"Database Management": "B", "Data Structures": "C", "Mathematics": "C"}
    }

@mcp.tool()
def search_scholarships_and_internships(department: str, cgpa: float, skills: list) -> dict:
    """
    Search institutional registries for matching scholarships, internships, hackathons, and certifications.
    
    Args:
        department: The student's department (e.g. 'CSE', 'ECE').
        cgpa: The student's current CGPA (float, e.g. 8.9).
        skills: A list of skills the student possesses (e.g. ['Python', 'Machine Learning']).
        
    Returns:
        A dictionary containing lists of matching scholarships and opportunities.
    """
    matching_scholarships = []
    for s in SCHOLARSHIPS_DATABASE:
        if cgpa >= s["min_cgpa"] and department.upper() in s["departments"]:
            matching_scholarships.append(s)
            
    matching_opportunities = []
    # Match opportunities based on department and overlap of skills
    skill_set = set(k.lower() for k in skills)
    for o in OPPORTUNITIES_DATABASE:
        dept_match = any(d.upper() == department.upper() for d in o.get("departments", []))
        req_skills = [s.lower() for s in o.get("required_skills", [])]
        skill_match = any(rs in skill_set for rs in req_skills) if req_skills else True
        
        if dept_match or skill_match:
            matching_opportunities.append(o)
            
    return {
        "scholarships": matching_scholarships,
        "opportunities": matching_opportunities
    }

@mcp.tool()
def fetch_career_roadmap_templates(career_goal: str) -> dict:
    """
    Retrieve structured career roadmaps, suggested hands-on projects, certification paths, and interview prep guides.
    
    Args:
        career_goal: Target career role (e.g. 'AI Engineer', 'Software Engineer').
        
    Returns:
        A dictionary containing certifications, projects, roadmap phases, and interview preparation guides.
    """
    goal_key = career_goal.lower().strip()
    if goal_key in CAREER_ROADMAPS:
        return CAREER_ROADMAPS[goal_key]
        
    # General software engineering fallback template
    return {
        "title": f"Professional {career_goal.capitalize()} Career Path",
        "certifications": [
            "AWS Certified Cloud Practitioner",
            "Google Professional Cloud Architect",
            "Oracle Certified Professional Java SE Developer"
        ],
        "projects": [
            {
                "name": "E-Commerce Microservices App",
                "description": "Design and build a scalable REST API using Node.js/Spring Boot and Docker containers.",
                "complexity": "Medium"
            },
            {
                "name": "Secure Web Application with OAuth2",
                "description": "Implement authentication and authorisation systems using JWT and HTTPS.",
                "complexity": "Medium"
            }
        ],
        "roadmap_phases": [
            {"phase": "Weeks 1-2: Foundations", "focus": "Algorithms, Data Structures, OOP principles, Clean Code"},
            {"phase": "Weeks 3-4: Frameworks", "focus": "Web frameworks, database modeling, REST API development"},
            {"phase": "Weeks 5-6: Cloud Infrastructure", "focus": "Docker, Kubernetes, AWS/GCP basics, CI/CD pipelines"},
            {"phase": "Weeks 7-8: Capstone Project", "focus": "Deploying a complete project and optimizing performance"}
        ],
        "interview_prep": [
            "Solve medium LeetCode algorithms on Data Structures (Trees, Graphs, Hash Maps).",
            "Review relational databases vs NoSQL, transaction ACID properties, and basic SQL optimization.",
            "Practice designing a scalable distributed system like a URL Shortener or Chat App."
        ]
    }

if __name__ == "__main__":
    # Start the fastmcp stdio server
    mcp.run()

import os
import sys
import time

def run_cli_demo():
    print("="*70)
    print("🛡️  EDUSHIELD AI: Autonomous Student Success & Dropout Prevention CLI Demo")
    print("="*70)
    print("Initializing Multi-Agent Workflow Session...")
    time.sleep(1)
    
    # Check if agents.py is accessible
    try:
        from agents import SimulationOrchestrator
    except ImportError as e:
        print(f"Error importing modules: {e}")
        return
        
    student_payload = {
        "name": "Lohitha",
        "department": "CSE",
        "cgpa": 8.9,
        "attendance": 82.0,
        "skills": ["Python", "Power BI", "Machine Learning"],
        "career_goal": "AI Engineer"
    }
    
    print(f"\nStudent Selected: {student_payload['name']} (Dept: {student_payload['department']})")
    print(f"Stats: CGPA: {student_payload['cgpa']} | Attendance: {student_payload['attendance']}%")
    print(f"Career Target: {student_payload['career_goal']}\n")
    print("Triggering ADK Agents sequential graph. Please wait...\n")
    
    try:
        # Run simulation with UTF-8 support
        steps = list(SimulationOrchestrator.run_simulation(student_payload))
        
        for idx, step in enumerate(steps):
            agent = step["agent"]
            report = step["output"]
            
            print(f"[{idx+1}/6] 🤖 {agent} is processing data...")
            time.sleep(1)
            print("-" * 50)
            print(report)
            print("-" * 50 + "\n")
            
        print("="*70)
        print("🛡️  EduShield AI: Multi-Agent Workflow Completed Successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"Workflow execution failed: {e}")

if __name__ == "__main__":
    # Force UTF-8 stdout encoding for printing emojis
    if sys.platform.startswith("win"):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    run_cli_demo()

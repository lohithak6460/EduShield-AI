import os
import sys

def generate_diagram():
    print("Generating EduShield AI Multi-Agent Architecture Diagram...")
    
    # Ensure docs directory exists
    os.makedirs("docs", exist_ok=True)
    
    try:
        from graphviz import Digraph
    except ImportError:
        print("Error: graphviz python package not installed. Run 'pip install graphviz'.")
        return False
        
    dot = Digraph('EduShield_Architecture', comment='EduShield AI Multi-Agent System')
    dot.attr(rankdir='TB', size='10,12', dpi='300')
    dot.attr('node', fontname='Helvetica,Arial,sans-serif', fontsize='11', shape='box', style='filled,rounded')
    dot.attr('edge', fontname='Helvetica,Arial,sans-serif', fontsize='9')
    
    # Define cohesive, premium color scheme (slate gray, teal, deep indigo)
    color_bg_agent = '#E0F2F1'      # Pale Teal for agents
    color_border_agent = '#00796B'  # Deep Teal border
    color_bg_mcp = '#E8EAF6'        # Pale Indigo for MCP
    color_border_mcp = '#3F51B5'    # Indigo border
    color_bg_io = '#ECEFF1'         # Slate gray for input/output
    color_border_io = '#455A64'     # Dark Slate
    
    # Input/Output Nodes
    dot.node('input', '📥 STUDENT INPUTS\n- Name, Dept, CGPA\n- Attendance, Skills, Goal', 
             fillcolor=color_bg_io, color=color_border_io, penwidth='2')
    dot.node('report', '🛡️ FINAL SUCCESS REPORT\n- Success Score\n- Risk Assessments\n- 30-Day Intervention Plan', 
             fillcolor=color_bg_io, color=color_border_io, penwidth='2', shape='doubleoctagon')
             
    # MCP Server & Tools
    dot.node('mcp_server', '🔌 Stdio MCP Database Server\n(FastMCP Host)', 
             fillcolor=color_bg_mcp, color=color_border_mcp, penwidth='2', shape='cylinder')
    dot.node('mcp_db', 'get_student_db_record()\nsearch_scholarships_and_internships()\nfetch_career_roadmap_templates()', 
             fillcolor=color_bg_mcp, color=color_border_mcp, style='filled,dashed,rounded')
             
    # ADK Agents (Sequential pipeline)
    dot.node('agent1', '1. Student Profile Agent\n[ADK Agent]\n- Resolves inputs\n- Builds unified profile', 
             fillcolor=color_bg_agent, color=color_border_agent, penwidth='1.5')
    dot.node('agent2', '2. Risk Assessment Agent\n[ADK Agent]\n- Academic & Dropout Risk\n- Skill Gap Identification', 
             fillcolor=color_bg_agent, color=color_border_agent, penwidth='1.5')
    dot.node('agent3', '3. Scholarship & Opportunity Agent\n[ADK Agent]\n- Scholarship matches\n- Certification discovery', 
             fillcolor=color_bg_agent, color=color_border_agent, penwidth='1.5')
    dot.node('agent4', '4. Learning Coach Agent\n[ADK Agent]\n- 30-Day customized study plan\n- Handpicked milestones', 
             fillcolor=color_bg_agent, color=color_border_agent, penwidth='1.5')
    dot.node('agent5', '5. Career Navigator Agent\n[ADK Agent]\n- Goal roadmap creation\n- Portfolio projects & prep', 
             fillcolor=color_bg_agent, color=color_border_agent, penwidth='1.5')
    dot.node('agent6', '6. Intervention Coordinator Agent\n[ADK Agent]\n- Success score formulation\n- Final report orchestration', 
             fillcolor=color_bg_agent, color=color_border_agent, penwidth='1.5')

    # Core workflow sequence edges (thick, blue arrow)
    dot.edge('input', 'agent1', label='START Workflow', color='#1E88E5', penwidth='2')
    dot.edge('agent1', 'agent2', label='Profile details', color='#1E88E5', penwidth='2')
    dot.edge('agent2', 'agent3', label='Risk & Gaps', color='#1E88E5', penwidth='2')
    dot.edge('agent3', 'agent4', label='Opportunity pool', color='#1E88E5', penwidth='2')
    dot.edge('agent4', 'agent5', label='Study milestones', color='#1E88E5', penwidth='2')
    dot.edge('agent5', 'agent6', label='Career roadmaps', color='#1E88E5', penwidth='2')
    dot.edge('agent6', 'report', label='END Workflow', color='#2E7D32', penwidth='2')
    
    # MCP Connection & Tool Calls
    dot.edge('mcp_server', 'mcp_db', dir='none', style='dashed', color=color_border_mcp)
    dot.edge('agent1', 'mcp_db', label='Query student DB', style='dotted', color='#5E35B1')
    dot.edge('agent3', 'mcp_db', label='Query scholarships & opportunities', style='dotted', color='#5E35B1')
    dot.edge('agent5', 'mcp_db', label='Fetch roadmap data', style='dotted', color='#5E35B1')

    # Output files
    output_path = os.path.join("docs", "architecture_diagram")
    try:
        # Render graphviz to PNG and remove source dot file
        dot.render(output_path, format='png', cleanup=True)
        print(f"Success! Diagram rendered to: {output_path}.png")
        return True
    except Exception as e:
        print("\n" + "="*60)
        print("WARNING: Graphviz executable not found on the system path.")
        print("The PNG file could not be generated. This is normal if Graphviz is not installed locally.")
        print("We have successfully saved the logic in graphviz python. A text-based representation")
        print("has been included in the README.md for display.")
        print("="*60 + "\n")
        
        # Save a backup .dot file so the code is inspectable
        try:
            dot.save(output_path + ".dot")
            print(f"Saved raw graph design file to: {output_path}.dot")
        except:
            pass
        return False

if __name__ == "__main__":
    generate_diagram()

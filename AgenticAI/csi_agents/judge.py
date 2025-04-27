import json
import subprocess
import threading
import socket
import os
from flask import Flask, jsonify
from agents.deployer import deploy_judging_form
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Azure AI Project connection
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str="westus3.api.azureml.ms;c5d47662-af4d-400e-ace6-ff70828d7d98;az-csi-grp1;agents"
)

# Your agent ID
support_agent_id = "asst_8MzgBgzJFqOPyhY96zMbXkbH"
def declare_winners():
    # Step 1: Load the judging JSON content
    with open('judging_data.json', 'r') as file:
        judging_content = file.read()

    # Step 2: Create a strong and clear prompt
    prompt = f"""
The following is the judging data collected from judges for different participant teams:

{judging_content}

Instructions for you:
- Calculate the final average score for each participant team across all judges.
- Rank the participants based on their overall average score, from highest to lowest.
- Clearly announce the 🥇 1st Place, 🥈 2nd Place, and 🥉 3rd Place winners.
- Show their names along with the final average score.
- Format your response cleanly for announcement.

Example Response Format:
1st Place 🥇: Team XYZ with Average Score 9.5
2nd Place 🥈: Team ABC with Average Score 9.2
3rd Place 🥉: Team DEF with Average Score 8.9
"""

    # Step 3: Create thread and send prompt
    thread = project_client.agents.create_thread()

    project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    run = project_client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=support_agent_id
    )

    messages = project_client.agents.list_messages(thread_id=thread.id)

    # Step 4: Print the Winner Announcement!
    print("\n🏆 Official Winners Announced:")
    print(messages.text_messages[0].text["value"])

# Initialize Flask app
app = Flask(__name__)

# --- Support Functions --- #

def setup_environment_logic():
    """Install required Python packages."""
    try:
        result = subprocess.run(['pip', 'install', '-r', 'requirements.txt'], capture_output=True, text=True)
        print("✅ Environment setup complete!")
    except Exception as e:
        print(f"❌ Environment setup failed: {str(e)}")

def get_local_ip():
    """Auto-detect your current LAN IP address dynamically."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

def deploy_judging_form_directly():
    """Start the judging form (app.py) automatically."""
    threading.Thread(target=lambda: subprocess.run(["python", "agents/app.py"])).start()

    local_ip = get_local_ip()
    public_url = f"http://{local_ip}:5000"
    print(f"\n🔗 Judges should open this link to access the form:")
    print(f"{public_url}\n")

    return public_url

# --- Flask Routes --- #

@app.route('/setup-environment', methods=['POST'])
def setup_environment():
    try:
        result = subprocess.run(['pip', 'install', '-r', 'requirements.txt'], capture_output=True, text=True)
        return jsonify({"message": "✅ Environment setup complete!", "output": result.stdout})
    except Exception as e:
        return jsonify({"message": f"❌ Error: {str(e)}"})

@app.route('/deploy-judging-form', methods=['POST'])
def deploy_form():
    try:
        public_url = deploy_judging_form()
        return jsonify({"url": public_url})
    except Exception as e:
        return jsonify({"error": str(e)})
    
@app.route('/declare-winners', methods=['POST'])
def declare_winners_api():
    try:
        declare_winners()
        return jsonify({"message": "🏆 Winners declared successfully! Check console for output."})
    except Exception as e:
        return jsonify({"error": str(e)})

# --- Main App Run --- #

def run_app():
    setup_environment_logic()          # ✅ Step 1: Setup
    deploy_judging_form_directly()      # ✅ Step 2: Deploy Form (no auto-open)
    app.run(host='0.0.0.0', port=8000)  # ✅ Step 3: Start backend server

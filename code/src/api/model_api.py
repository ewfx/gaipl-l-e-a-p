import json
import ollama
import re
from typing import Dict, Tuple, Optional, List
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

CONFIG = {
    "servicenow_file": "servicenow_inc.json",
    "dashboards_file": "dashboard_mapping.json",
    "observability_file": "observability_data.json",
    "cmdb_file": "cmdb_data.json",
    "llm_model": "mistral"
}

def load_json(file_path: str) -> Dict:
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def get_dashboard_link(ci: str, dashboards: Dict) -> str:
    return dashboards.get(ci.lower(), "No dashboard available")

def get_ci_health_status(ci: str, observability_data: list) -> Dict[str, str]:
    for entry in observability_data:
        if entry["ci"].lower() == ci.lower():
            prompt = f"""
            Given the following observability data for a Configuration Item (CI):
            - CPU Usage: {entry.get('cpu_usage', 'N/A')}
            - Memory Usage: {entry.get('memory_usage', 'N/A')}
            - Disk Usage: {entry.get('disk_usage', 'N/A')}
            - Status: {entry["status"]}

            Generate a concise health status message explaining the CI health in a user-friendly manner.
            """
            try:
                response = ollama.chat(
                    model=CONFIG["llm_model"],
                    messages=[{"role": "user", "content": prompt}]
                )
                message = response['message']['content'].strip()
            except Exception as e:
                message = "No additional health details available."
            return {"status": entry["status"], "message": message}
    return {"status": "Unknown", "message": "No observability data available"}

def get_observability_updates(ci: str, observability_data: list) -> str:
    for entry in observability_data:
        if entry["ci"].lower() == ci.lower():
            return entry.get("updates", "No recent updates available.")
    return "No observability updates available."

def detect_intent(user_query: str, context: Dict) -> Tuple[str, str]:
    prompt = (
        f"Determine the primary intent and sub-intent (if applicable) of the following user query: '{user_query}'. "
        "Provide intent as one of: 1. Incident Status Inquiry, 2. CI Health Check, 3. Dependency Impact Analysis, "
        "4. Recommendations Search, 5. Automation Execution, 6. List Open Incidents with CI Health, 7. General Queries. "
        "Sub-intent should be 'None' unless a specific detail is clear (e.g., 'Upstream' or 'Downstream' for Dependency Impact Analysis). "
        "Return ONLY in this format: Intent: <intent>, Sub-intent: <sub-intent>. "
        "Examples: "
        "'Tell me about INC12345' -> Intent: Incident Status Inquiry, Sub-intent: None; "
        "'Check health of ServerX' -> Intent: CI Health Check, Sub-intent: None; "
        "'Check upstream for DB-PROD-03' -> Intent: Dependency Impact Analysis, Sub-intent: Upstream; "
        "'Can you also give me health status' -> Intent: CI Health Check, Sub-intent: None (assume context if no CI specified)."
    )
    try:
        response = ollama.chat(
            model=CONFIG["llm_model"],
            messages=[{"role": "user", "content": prompt}]
        )
        intent_response = response['message']['content'].strip()
        intent_match = re.search(r"Intent: (.+?)(?:, Sub-intent: (.+))?$", intent_response)
        if intent_match:
            intent, sub_intent = intent_match.groups()
            return intent, sub_intent if sub_intent else "None"
        return "General Queries", "None"
    except Exception as e:
        return "Error", "None"

def extract_incident_id(user_query: str) -> Optional[str]:
    match = re.search(r"INC\d+", user_query, re.IGNORECASE)
    return match.group(0) if match else None

def extract_ci_name(user_query: str, servicenow_data: list, context: Dict) -> Optional[str]:
    incident_id = extract_incident_id(user_query)
    if incident_id:
        incident = next((i for i in servicenow_data if i["id"].lower() == incident_id.lower()), None)
        if incident and "affected_ci" in incident:
            return incident["affected_ci"]
    patterns = [
        r"for ([a-zA-Z0-9-_]+)",
        r"of ([a-zA-Z0-9-_]+)",
        r"with ([a-zA-Z0-9-_]+)",
        r"([a-zA-Z0-9-_]+)\s*(health|status|staus|dependencies|upstream|downstream)"
    ]
    for pattern in patterns:
        match = re.search(pattern, user_query, re.IGNORECASE)
        if match:
            ci_candidate = match.group(1)
            if ci_candidate.lower() not in ["me", "you", "it", "this", "that"]:
                return ci_candidate
    return context.get("last_ci")

def get_ci_dependencies(ci_name: str, cmdb_data: list) -> Dict[str, List[Dict]]:
    for entry in cmdb_data:
        if entry["ci"].lower() == ci_name.lower():
            return {
                "upstream": entry.get("upstream", []),
                "downstream": entry.get("downstream", [])
            }
    return {"upstream": [], "downstream": []}

def process_query(user_query: str, context: Dict, servicenow_data: list, dashboards: Dict, observability_data: list, cmdb_data: list) -> Dict:
    intent, sub_intent = detect_intent(user_query, context)
    
    if "INC" in user_query.upper() and intent == "General Queries":
        intent = "Incident Status Inquiry"
    if ("health" in user_query.lower() or "status" in user_query.lower() or "staus" in user_query.lower()) and intent == "General Queries" and context.get("last_ci"):
        intent = "CI Health Check"
    if ("upstream" in user_query.lower() or "downstream" in user_query.lower() or "dependencies" in user_query.lower()) and intent == "General Queries":
        intent = "Dependency Impact Analysis"

    response = {"intent": intent, "sub_intent": sub_intent, "response": {}}

    incident_id = extract_incident_id(user_query)
    if incident_id:
        context["last_incident_id"] = incident_id

    ci_name = extract_ci_name(user_query, servicenow_data, context)
    if ci_name:
        context["last_ci"] = ci_name

    if intent == "Incident Status Inquiry":
        incident_id = incident_id or context.get("last_incident_id")
        if incident_id:
            incident = next((i for i in servicenow_data if i["id"].lower() == incident_id.lower()), None)
            if incident:
                dashboard_link = get_dashboard_link(incident["affected_ci"], dashboards)
                context["last_ci"] = incident["affected_ci"]
                dependencies = get_ci_dependencies(incident["affected_ci"], cmdb_data)
                response["response"] = {
                    "incident_id": incident_id,
                    "impacted_ci": incident["affected_ci"],
                    "status": incident["status"],
                    "description": incident["description"],
                    "dashboard": dashboard_link,
                    "dependencies": dependencies
                }
            else:
                response["response"] = {"message": f"Incident {incident_id} not found."}
        else:
            open_incidents = [i for i in servicenow_data if i["status"].lower() not in ["resolved", "closed"]]
            response["response"] = {
                "message": f"Found {len(open_incidents)} open incidents" if open_incidents else "No open incidents found",
                "incidents": [{"id": i["id"], "short_description": i["short_description"], "status": i["status"]} for i in open_incidents]
            }

    elif intent == "CI Health Check":
        ci_name = ci_name or context.get("last_ci")
        incident_id = incident_id or context.get("last_incident_id")
        if ci_name:
            health_status = get_ci_health_status(ci_name, observability_data)
            updates = get_observability_updates(ci_name, observability_data)
            dashboard_link = get_dashboard_link(ci_name, dashboards)
            dependencies = get_ci_dependencies(ci_name, cmdb_data)
            prefix = f"Affected CI for {incident_id}" if incident_id else "CI"
            response["response"] = {
                "ci": ci_name,
                "prefix": prefix,
                "health_status": health_status["status"],
                "details": health_status["message"],
                "recent_updates": updates,
                "dashboard": dashboard_link,
                "dependencies": dependencies
            }
        else:
            response["response"] = {"message": "Please specify a CI or provide an incident ID."}

    elif intent == "List Open Incidents with CI Health":
        open_incidents = [i for i in servicenow_data if i["status"].lower() not in ["resolved", "closed"]]
        if open_incidents:
            incidents_list = []
            for incident in open_incidents:
                ci_name = incident.get("affected_ci", "Unknown CI")
                health_status = get_ci_health_status(ci_name, observability_data)
                incidents_list.append({
                    "incident_id": incident["id"],
                    "ci": ci_name,
                    "status": incident["status"],
                    "ci_health": health_status["status"],
                    "details": health_status["message"]
                })
            response["response"] = {
                "message": f"Found {len(open_incidents)} open incidents",
                "incidents": incidents_list
            }
        else:
            response["response"] = {"message": "No open incidents found."}

    elif intent == "Dependency Impact Analysis":
        ci_name = ci_name or context.get("last_ci")
        if ci_name:
            dependencies = get_ci_dependencies(ci_name, cmdb_data)
            response["response"] = {
                "ci": ci_name,
                "dependencies": dependencies
            }
        else:
            response["response"] = {"message": "Please specify a CI for dependency analysis."}

    elif intent == "Recommendations Search":
        incident_id = incident_id or context.get("last_incident_id")
        response["response"] = {
            "message": f"Searching recommendations for {incident_id} is not yet implemented." if incident_id else "Please provide an incident ID for recommendations."
        }

    elif intent == "Automation Execution":
        ci_name = ci_name or context.get("last_ci")
        response["response"] = {
            "message": f"Automation execution for {ci_name} is not yet implemented." if ci_name else "Please specify a CI or incident for automation."
        }

    else:
        response["response"] = {"message": "I’m still learning! Try asking about incidents or CI health."}

    return response

# Load data once at startup
servicenow_data = load_json(CONFIG["servicenow_file"])
dashboards = load_json(CONFIG["dashboards_file"])
observability_data = load_json(CONFIG["observability_file"])
cmdb_data = load_json(CONFIG["cmdb_file"])

# In-memory context (for simplicity; in production, use a database or session store)
context = {"last_incident_id": None, "last_ci": None}

@app.route('/query', methods=['POST'])
def handle_query():
    if not all([servicenow_data, dashboards, observability_data, cmdb_data]):
        return jsonify({"error": "Critical data files are missing or invalid."}), 500

    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    user_query = data["query"]
    if user_query.lower() == "exit":
        return jsonify({"message": "Goodbye!"}), 200

    result = process_query(user_query, context, servicenow_data, dashboards, observability_data, cmdb_data)
    return jsonify(result), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

import json
import ollama
import re
from typing import Dict, Tuple, Optional, List

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
        print(f"Error: File {file_path} not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {file_path}.")
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
                print(f"Error generating message from Ollama: {e}")
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
        print(f"Error detecting intent: {e}")
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

def list_open_incidents_with_ci_health(servicenow_data: list, observability_data: list) -> None:
    open_incidents = [i for i in servicenow_data if i["status"].lower() not in ["resolved", "closed"]]
    if not open_incidents:
        print("No open incidents found.")
        return
    print(f"Found {len(open_incidents)} open incidents with CI health statuses:")
    for incident in open_incidents:
        ci_name = incident.get("affected_ci", "Unknown CI")
        health_status = get_ci_health_status(ci_name, observability_data)
        print(f"- Incident {incident['id']} (CI: {ci_name})")
        print(f"  - Status: {incident['status']}")
        print(f"  - CI Health: {health_status['status']}")
        print(f"  - Details: {health_status['message']}")

def display_dependencies(ci_name: str, cmdb_data: list, indent: str = "  ") -> None:
    dependencies = get_ci_dependencies(ci_name, cmdb_data)
    print(f"{indent}Dependencies for {ci_name}:")
    if dependencies["upstream"]:
        print(f"{indent}- Upstream:")
        for dep in dependencies["upstream"]:
            print(f"{indent}  - {dep['ci']} ({dep['type']}, {dep['relationship']})")
    else:
        print(f"{indent}- Upstream: None")
    if dependencies["downstream"]:
        print(f"{indent}- Downstream:")
        for dep in dependencies["downstream"]:
            print(f"{indent}  - {dep['ci']} ({dep['type']}, {dep['relationship']})")
    else:
        print(f"{indent}- Downstream: None")

def main():
    servicenow_data = load_json(CONFIG["servicenow_file"])
    dashboards = load_json(CONFIG["dashboards_file"])
    observability_data = load_json(CONFIG["observability_file"])
    cmdb_data = load_json(CONFIG["cmdb_file"])

    if not all([servicenow_data, dashboards, observability_data, cmdb_data]):
        print("Critical data files are missing or invalid. Exiting.")
        return

    context = {"last_incident_id": None, "last_ci": None}
    print("OpsBuddy is ready! Type 'exit' to quit.")
    while True:
        user_query = input("Enter your query: ").strip()
        if user_query.lower() == "exit":
            print("Goodbye!")
            break

        intent, sub_intent = detect_intent(user_query, context)
        
        if "INC" in user_query.upper() and intent == "General Queries":
            intent = "Incident Status Inquiry"
        if ("health" in user_query.lower() or "status" in user_query.lower() or "staus" in user_query.lower()) and intent == "General Queries" and context.get("last_ci"):
            intent = "CI Health Check"
        if ("upstream" in user_query.lower() or "downstream" in user_query.lower() or "dependencies" in user_query.lower()) and intent == "General Queries":
            intent = "Dependency Impact Analysis"

        print(f"Detected Intent: {intent}, Sub-intent: {sub_intent}\n")

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
                    print(f"Incident {incident_id} Details:")
                    print(f"- Impacted CI: {incident['affected_ci']}")
                    print(f"- Status: {incident['status']}")
                    print(f"- Description: {incident['description']}")
                    print(f"- Dashboard: {dashboard_link}")
                    display_dependencies(incident["affected_ci"], cmdb_data)
                else:
                    print(f"Incident {incident_id} not found.")
            else:
                open_incidents = [i for i in servicenow_data if i["status"].lower() not in ["resolved", "closed"]]
                if open_incidents:
                    print(f"Found {len(open_incidents)} open incidents:")
                    for i in open_incidents:
                        print(f"- {i['id']}: {i['short_description']} (Status: {i['status']})")
                else:
                    print("No open incidents found.")

        elif intent == "CI Health Check":
            ci_name = ci_name or context.get("last_ci")
            incident_id = incident_id or context.get("last_incident_id")
            if ci_name:
                health_status = get_ci_health_status(ci_name, observability_data)
                updates = get_observability_updates(ci_name, observability_data)
                dashboard_link = get_dashboard_link(ci_name, dashboards)
                prefix = f"Affected CI for {incident_id}" if incident_id else "CI"
                print(f"{prefix}: {ci_name}")
                print(f"- Health Status: {health_status['status']}")
                print(f"- Details: {health_status['message']}")
                print(f"- Recent Updates: {updates}")
                print(f"- Dashboard: {dashboard_link}")
                display_dependencies(ci_name, cmdb_data)
            else:
                print("Please specify a CI or provide an incident ID.")

        elif intent == "List Open Incidents with CI Health":
            list_open_incidents_with_ci_health(servicenow_data, observability_data)

        elif intent == "Dependency Impact Analysis":
            ci_name = ci_name or context.get("last_ci")
            if ci_name:
                print(f"Dependency Impact Analysis for {ci_name}:")
                display_dependencies(ci_name, cmdb_data)
            else:
                print("Please specify a CI for dependency analysis.")

        elif intent == "Recommendations Search":
            incident_id = incident_id or context.get("last_incident_id")
            if incident_id:
                print(f"Searching recommendations for {incident_id} is not yet implemented.")
            else:
                print("Please provide an incident ID for recommendations.")

        elif intent == "Automation Execution":
            ci_name = ci_name or context.get("last_ci")
            if ci_name:
                print(f"Automation execution for {ci_name} is not yet implemented.")
            else:
                print("Please specify a CI or incident for automation.")

        else:
            print("I’m still learning! Try asking about incidents or CI health.")

if __name__ == "__main__":
    main()

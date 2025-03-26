import unittest
from unittest.mock import patch, Mock
from flask import Flask
from your_app_file import app, load_json, detect_intent, extract_ci_name, get_ci_health_status, process_query  # Replace 'your_app_file' with actual filename

# Mock data for testing
mock_servicenow_data = [
    {"id": "INC12345", "affected_ci": "ServerX", "status": "Open", "description": "Server down"},
    {"id": "INC12346", "affected_ci": "DB-PROD-03", "status": "Resolved", "description": "DB failure"}
]
mock_dashboards = {"serverx": "http://dashboard.com/serverx"}
mock_observability_data = [
    {"ci": "ServerX", "status": "Critical", "cpu_usage": "90%", "memory_usage": "85%", "disk_usage": "95%", "updates": "High load detected"}
]
mock_cmdb_data = [
    {"ci": "ServerX", "upstream": [{"ci": "RouterA"}], "downstream": [{"ci": "AppB"}]}
]
mock_context = {"last_incident_id": None, "last_ci": None}

class TestOpsBuddyBackend(unittest.TestCase):

    def setUp(self):
        # Set up Flask test client
        self.app = app.test_client()
        self.app.testing = True

    # Test 1: API Endpoint - Successful Query
    @patch('your_app_file.client.chat.completions.create')
    def test_query_endpoint_success(self, mock_openai):
        mock_openai.return_value = Mock(choices=[Mock(message=Mock(content="Intent: Incident Status Inquiry, Sub-intent: None"))])
        response = self.app.post('/query', json={"query": "Tell me about INC12345"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["intent"], "Incident Status Inquiry")
        self.assertIn("incident_id", data["response"])

    # Test 2: API Endpoint - Missing Query
    def test_query_endpoint_missing_query(self):
        response = self.app.post('/query', json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Missing 'query' in request body")

    # Test 3: API Endpoint - Exit Command
    def test_query_endpoint_exit(self):
        response = self.app.post('/query', json={"query": "exit"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["message"], "Goodbye!")

    # Test 4: Intent Detection - Incident Status Inquiry
    @patch('your_app_file.client.chat.completions.create')
    def test_detect_intent_incident_status(self, mock_openai):
        mock_openai.return_value = Mock(choices=[Mock(message=Mock(content="Intent: Incident Status Inquiry, Sub-intent: None"))])
        intent, sub_intent = detect_intent("Tell me about INC12345", {})
        self.assertEqual(intent, "Incident Status Inquiry")
        self.assertEqual(sub_intent, "None")

    # Test 5: Intent Detection - CI Health Check
    @patch('your_app_file.client.chat.completions.create')
    def test_detect_intent_ci_health(self, mock_openai):
        mock_openai.return_value = Mock(choices=[Mock(message=Mock(content="Intent: CI Health Check, Sub-intent: None"))])
        intent, sub_intent = detect_intent("Check health of ServerX", {})
        self.assertEqual(intent, "CI Health Check")
        self.assertEqual(sub_intent, "None")

    # Test 6: Intent Detection - Dependency Analysis with Sub-intent
    @patch('your_app_file.client.chat.completions.create')
    def test_detect_intent_dependency_upstream(self, mock_openai):
        mock_openai.return_value = Mock(choices=[Mock(message=Mock(content="Intent: Dependency Impact Analysis, Sub-intent: Upstream"))])
        intent, sub_intent = detect_intent("Check upstream for DB-PROD-03", {})
        self.assertEqual(intent, "Dependency Impact Analysis")
        self.assertEqual(sub_intent, "Upstream")

    # Test 7: CI Extraction - From Incident ID
    def test_extract_ci_name_from_incident(self):
        ci_name = extract_ci_name("Tell me about INC12345", mock_servicenow_data, {})
        self.assertEqual(ci_name, "ServerX")

    # Test 8: CI Extraction - From Query Pattern
    def test_extract_ci_name_from_query(self):
        ci_name = extract_ci_name("Check health of ServerX", mock_servicenow_data, {})
        self.assertEqual(ci_name, "ServerX")

    # Test 9: CI Extraction - From Context
    def test_extract_ci_name_from_context(self):
        context = {"last_ci": "DB-PROD-03"}
        ci_name = extract_ci_name("What’s the status?", mock_servicenow_data, context)
        self.assertEqual(ci_name, "DB-PROD-03")

    # Test 10: Health Status - Valid CI
    @patch('your_app_file.client.chat.completions.create')
    def test_get_ci_health_status_valid(self, mock_openai):
        mock_openai.return_value = Mock(choices=[Mock(message=Mock(content="ServerX is in critical condition due to high resource usage."))])
        health = get_ci_health_status("ServerX", mock_observability_data)
        self.assertEqual(health["status"], "Critical")
        self.assertIn("critical condition", health["message"])

    # Test 11: Health Status - Unknown CI
    def test_get_ci_health_status_unknown(self):
        health = get_ci_health_status("UnknownCI", mock_observability_data)
        self.assertEqual(health["status"], "Unknown")
        self.assertEqual(health["message"], "No observability data available")

    # Test 12: File Loading - Valid File
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"key": "value"}')
    def test_load_json_valid(self, mock_file):
        data = load_json("dummy.json")
        self.assertEqual(data, {"key": "value"})

    # Test 13: File Loading - File Not Found
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_json_not_found(self, mock_file):
        data = load_json("missing.json")
        self.assertEqual(data, {})

    # Test 14: Query Processing - Incident Status Inquiry
    @patch('your_app_file.client.chat.completions.create')
    def test_process_query_incident_status(self, mock_openai):
        mock_openai.return_value = Mock(choices=[Mock(message=Mock(content="Intent: Incident Status Inquiry, Sub-intent: None"))])
        result = process_query("Tell me about INC12345", mock_context, mock_servicenow_data, mock_dashboards, mock_observability_data, mock_cmdb_data)
        self.assertEqual(result["intent"], "Incident Status Inquiry")
        self.assertEqual(result["response"]["incident_id"], "INC12345")
        self.assertEqual(result["response"]["impacted_ci"], "ServerX")

    # Test 15: Query Processing - CI Health Check
    @patch('your_app_file.client.chat.completions.create')
    def test_process_query_ci_health(self, mock_openai):
        mock_openai.side_effect = [
            Mock(choices=[Mock(message=Mock(content="Intent: CI Health Check, Sub-intent: None"))]),  # Intent detection
            Mock(choices=[Mock(message=Mock(content="ServerX is in critical condition."))])  # Health status
        ]
        result = process_query("Check health of ServerX", mock_context, mock_servicenow_data, mock_dashboards, mock_observability_data, mock_cmdb_data)
        self.assertEqual(result["intent"], "CI Health Check")
        self.assertEqual(result["response"]["ci"], "ServerX")
        self.assertEqual(result["response"]["health_status"], "Critical")

if __name__ == '__main__':
    unittest.main()

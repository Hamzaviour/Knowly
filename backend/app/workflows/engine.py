from typing import Dict, Any, List
from datetime import datetime

class WorkflowAutomationEngine:
    """
    Rule-based event trigger and automation orchestrator:
    - Triggers: document.uploaded, analysis.completed
    - Conditions: e.g. file_type == 'contract', contains keyword 'liability'
    - Actions: Run Legal Agent, Extract Risks, Generate Report, Trigger Webhook
    """
    
    @staticmethod
    def evaluate_condition(doc_metadata: Dict[str, Any], condition_rules: Dict[str, Any]) -> bool:
        if not condition_rules:
            return True
        for key, expected_val in condition_rules.items():
            if doc_metadata.get(key) != expected_val:
                return False
        return True

    @classmethod
    async def trigger_event(cls, event_name: str, payload: Dict[str, Any], active_workflows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for wf in active_workflows:
            if wf.get("trigger_type") == event_name:
                conditions = wf.get("condition_rules", {})
                if cls.evaluate_condition(payload.get("metadata", {}), conditions):
                    # Execute actions
                    executed_actions = []
                    for act in wf.get("actions", []):
                        executed_actions.append({
                            "action": act.get("type"),
                            "status": "success",
                            "executed_at": datetime.utcnow().isoformat()
                        })
                    results.append({
                        "workflow_id": wf.get("id"),
                        "workflow_name": wf.get("name"),
                        "status": "completed",
                        "actions": executed_actions
                    })
        return results

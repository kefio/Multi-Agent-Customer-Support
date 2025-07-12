"""
Flight Workflow - Contains all flight-related nodes and routing logic.

This module defines:
- Flight entry node (enter_update_flight) 
- Flight assistant node (update_flight)
- Flight tools nodes (safe and sensitive)
- Flight leave node (leave_skill)
- Flight routing function
"""

from typing import Dict, Any
from customer_support_agent.state import State
from customer_support_agent.utils import Assistant, create_tool_node_with_fallback, create_entry_node, pop_dialog_state
from customer_support_agent.assistants.flight import update_flight_runnable, update_flight_safe_tools, update_flight_sensitive_tools
from customer_support_agent.tools import CompleteOrEscalate

# === FLIGHT WORKFLOW NODES ===
# Direct assignment - these functions are already callable nodes

flight_entry_node = create_entry_node("Flight Updates & Booking Assistant", "update_flight")
flight_assistant_node = Assistant(update_flight_runnable)
flight_safe_tools_node = create_tool_node_with_fallback(update_flight_safe_tools)
flight_sensitive_tools_node = create_tool_node_with_fallback(update_flight_sensitive_tools)
flight_leave_node = pop_dialog_state

# === FLIGHT ROUTING FUNCTION ===

def route_update_flight(state: State) -> str:
    """
    Routing function for flight workflow.
    Determines which tools to use based on AI message content.
    """
    messages = state.get("messages", [])
    if not messages:
        return "leave_skill"
    
    last_ai_message = messages[-1]
    if not hasattr(last_ai_message, 'tool_calls') or not last_ai_message.tool_calls:
        return "leave_skill"
    
    tool_calls = last_ai_message.tool_calls

    # Check if user wants to cancel/escalate
    did_cancel = any(tool_call["name"] == CompleteOrEscalate.__name__ for tool_call in tool_calls)
    if did_cancel:
        return "leave_skill"
    
    # Check if all tools are safe tools
    safe_tools_name = [tool.name for tool in update_flight_safe_tools]
    if all(tool_call["name"] in safe_tools_name for tool_call in tool_calls):
        return "update_flight_safe_tools"
    
    # Otherwise use sensitive tools
    return "update_flight_sensitive_tools"

# === EXPORTS FOR REFERENCE ===
# Tools lists (for reference)
flight_safe_tools = update_flight_safe_tools
flight_sensitive_tools = update_flight_sensitive_tools 
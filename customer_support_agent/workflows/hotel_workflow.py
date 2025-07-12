"""
Hotel Workflow - Contains all hotel-related nodes and routing logic.

This module defines:
- Hotel entry node (enter_book_hotel)
- Hotel assistant node (book_hotel) 
- Hotel tools nodes (safe and sensitive)
- Hotel leave node (leave_skill)
- Hotel routing function
"""

from typing import Dict, Any
from customer_support_agent.state import State
from customer_support_agent.utils import Assistant, create_tool_node_with_fallback, create_entry_node, pop_dialog_state
from customer_support_agent.assistants.hotel import book_hotel_runnable, safe_tools, sensitive_tools
from customer_support_agent.tools import CompleteOrEscalate

# === HOTEL WORKFLOW NODES ===
# Direct assignment - these functions are already callable nodes

hotel_entry_node = create_entry_node("Hotel Booking Assistant", "book_hotel")
hotel_assistant_node = Assistant(book_hotel_runnable)
hotel_safe_tools_node = create_tool_node_with_fallback(safe_tools)
hotel_sensitive_tools_node = create_tool_node_with_fallback(sensitive_tools)
hotel_leave_node = pop_dialog_state

# === HOTEL WORKFLOW ROUTING ===

def route_book_hotel(state: State) -> str:
    """
    Route hotel workflow based on tool calls.
    
    Routing logic:
    - CompleteOrEscalate tool call → leave_skill  
    - All safe tools → book_hotel_safe_tools
    - Otherwise → book_hotel_sensitive_tools
    """
    messages = state.get("messages", [])
    if not messages:
        return "END"

    last_message = messages[-1]
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return "END"
        
    tool_calls = last_message.tool_calls
    
    # Check for CompleteOrEscalate (leave workflow)
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    
    # Check if all tools are safe tools
    safe_tool_names = [t.name for t in safe_tools]
    if all(tc["name"] in safe_tool_names for tc in tool_calls):
        return "book_hotel_safe_tools"
    
    # Otherwise use sensitive tools
    return "book_hotel_sensitive_tools" 
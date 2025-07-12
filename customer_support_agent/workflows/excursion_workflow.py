"""
Excursion Workflow - Contains all excursion-related nodes and routing logic.

This module defines:
- Excursion entry node (enter_book_excursion)
- Excursion assistant node (book_excursion)
- Excursion tools nodes (safe and sensitive)
- Excursion leave node (leave_skill)  
- Excursion routing function
"""

from typing import Dict, Any
from customer_support_agent.state import State
from customer_support_agent.utils import Assistant, create_tool_node_with_fallback, create_entry_node, pop_dialog_state
from customer_support_agent.assistants.excursion import (
    book_excursion_runnable,
    book_excursion_safe_tools as safe_tools, 
    book_excursion_sensitive_tools as sensitive_tools
)
from customer_support_agent.tools import CompleteOrEscalate

# === EXCURSION WORKFLOW NODES ===
# Direct assignment - these functions are already callable nodes

excursion_entry_node = create_entry_node("Excursion Booking Assistant", "book_excursion")
excursion_assistant_node = Assistant(book_excursion_runnable)
excursion_safe_tools_node = create_tool_node_with_fallback(safe_tools)
excursion_sensitive_tools_node = create_tool_node_with_fallback(sensitive_tools)
excursion_leave_node = pop_dialog_state

# === EXCURSION WORKFLOW ROUTING ===

def route_book_excursion(state: State) -> str:
    """
    Route excursion workflow based on tool calls.
    
    Routing logic:
    - CompleteOrEscalate tool call → leave_skill  
    - All safe tools → book_excursion_safe_tools
    - Otherwise → book_excursion_sensitive_tools
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
        return "book_excursion_safe_tools"
    
    # Otherwise use sensitive tools
    return "book_excursion_sensitive_tools" 
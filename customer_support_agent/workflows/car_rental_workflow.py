"""
Car Rental Workflow - Contains all car rental-related nodes and routing logic.

This module defines:
- Car rental entry node (enter_book_car_rental)
- Car rental assistant node (book_car_rental)
- Car rental tools nodes (safe and sensitive)  
- Car rental leave node (leave_skill)
- Car rental routing function
"""

from typing import Dict, Any
from customer_support_agent.state import State
from customer_support_agent.utils import Assistant, create_tool_node_with_fallback, create_entry_node, pop_dialog_state
from customer_support_agent.assistants.car_rental import (
    book_car_rental_runnable, 
    book_car_rental_safe_tools as safe_tools, 
    book_car_rental_sensitive_tools as sensitive_tools
)
from customer_support_agent.tools import CompleteOrEscalate

# === CAR RENTAL WORKFLOW NODES ===
# Direct assignment - these functions are already callable nodes

car_rental_entry_node = create_entry_node("Car Rental Assistant", "book_car_rental")
car_rental_assistant_node = Assistant(book_car_rental_runnable)
car_rental_safe_tools_node = create_tool_node_with_fallback(safe_tools)
car_rental_sensitive_tools_node = create_tool_node_with_fallback(sensitive_tools)
car_rental_leave_node = pop_dialog_state

# === CAR RENTAL WORKFLOW ROUTING ===

def route_book_car_rental(state: State) -> str:
    """
    Route car rental workflow based on tool calls.
    
    Routing logic:
    - CompleteOrEscalate tool call → leave_skill  
    - All safe tools → book_car_rental_safe_tools
    - Otherwise → book_car_rental_sensitive_tools
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
        return "book_car_rental_safe_tools"
    
    # Otherwise use sensitive tools
    return "book_car_rental_sensitive_tools" 
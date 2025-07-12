"""
Routing Module - Contains all routing functions for the main graph.

This module centralizes routing logic following the original notebook pattern:
- route_primary_assistant: Routes from primary assistant to entry points
- route_to_workflow: Routes from user input to appropriate workflow assistants

Based on the original LangGraph tutorial architecture.
"""

from typing import Literal
from customer_support_agent.state import State
from customer_support_agent.tools import ToFlightBookingAssistant, ToBookCarRental, ToHotelBookingAssistant, ToBookExcursion
from langgraph.graph import END


def route_primary_assistant(state: State) -> str:
    """
    Route from primary assistant to appropriate entry points based on tool calls.
    
    This follows the original notebook pattern where tool calls from the primary
    assistant route to entry points (enter_*) for first-time delegation.
    """
    messages = state.get("messages", [])
    if not messages:
        return END
    
    last_message = messages[-1]
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return END
    
    tool_calls = last_message.tool_calls
    if not tool_calls:
        return END
        
    tool_name = tool_calls[0]["name"]
    
    # Route to entry points for delegation (original notebook pattern)
    # ALL WORKFLOWS IMPLEMENTED STEP 3
    if tool_name == ToFlightBookingAssistant.__name__:
        return "enter_update_flight"
    elif tool_name == ToBookCarRental.__name__:
        return "enter_book_car_rental"
    elif tool_name == ToHotelBookingAssistant.__name__:
        return "enter_book_hotel"
    elif tool_name == ToBookExcursion.__name__:
        return "enter_book_excursion"
    else:
        return "primary_assistant_tools"


def route_to_workflow(state: State) -> Literal[
    "primary_assistant",
    "update_flight", 
    "book_car_rental",
    "book_hotel", 
    "book_excursion"
]:
    """
    Route from user input to appropriate workflow assistant nodes.
    
    This follows the original notebook pattern where continued conversations
    route directly to the assistant nodes (not entry points) based on dialog_state.
    
    Key difference from route_primary_assistant:
    - This routes to assistant nodes directly (update_flight, book_car_rental, etc.)
    - route_primary_assistant routes to entry points (enter_update_flight, etc.)
    """
    dialog_state = state.get("dialog_state", [])
    if not dialog_state:
        return "primary_assistant"
    
    # ALL WORKFLOWS IMPLEMENTED STEP 3
    current_workflow = dialog_state[-1]
    
    # Check if it's a supported workflow
    supported_workflows = ["update_flight", "book_car_rental", "book_hotel", "book_excursion"]
    if current_workflow in supported_workflows:
        return current_workflow
    else:
        # Fallback to primary_assistant for unknown workflows
        return "primary_assistant"


# === WORKFLOW-SPECIFIC ROUTING ===
# Import workflow routing functions - ALL IMPLEMENTED STEP 3

from customer_support_agent.workflows.flight_workflow import route_update_flight
from customer_support_agent.workflows.hotel_workflow import route_book_hotel
from customer_support_agent.workflows.car_rental_workflow import route_book_car_rental  
from customer_support_agent.workflows.excursion_workflow import route_book_excursion 
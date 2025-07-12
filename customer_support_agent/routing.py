"""
Routing Module - Intelligent Conversation Flow Management for Multi-Workflow System

This module centralizes all routing logic for the Swiss Airlines Customer Support AI,
implementing intelligent conversation flow management that seamlessly transitions
between the primary assistant and specialized workflow assistants. The routing
system follows the original LangGraph tutorial architecture while providing
sophisticated conversation state management.

Routing Philosophy:
    The routing system implements a dual-layer approach:
    
    1. Delegation Routing (route_primary_assistant):
       - Routes tool calls from primary assistant to workflow entry points
       - Handles first-time delegation to specialized assistants
       - Uses tool call analysis to determine appropriate workflow
    
    2. Continuation Routing (route_to_workflow):
       - Routes user messages to appropriate workflow assistants
       - Maintains conversation context within active workflows
       - Uses dialog state tracking for seamless workflow continuity

Key Design Patterns:
    - Entry Points vs. Assistant Nodes: Distinguishes between workflow initiation
      and workflow continuation for optimal conversation flow
    - State-Aware Routing: Leverages dialog_state for context-aware decisions
    - Fallback Mechanisms: Provides graceful degradation for edge cases
    - Scalable Architecture: Easy addition of new workflows and routing rules

Functions:
    route_primary_assistant: Routes tool calls to workflow entry points
    route_to_workflow: Routes user input to appropriate workflow assistants
    
Imported Workflow Routing:
    route_update_flight: Flight workflow tool routing
    route_book_hotel: Hotel workflow tool routing  
    route_book_car_rental: Car rental workflow tool routing
    route_book_excursion: Excursion workflow tool routing
"""

from typing import Literal
from customer_support_agent.state import State
from customer_support_agent.tools import ToFlightBookingAssistant, ToBookCarRental, ToHotelBookingAssistant, ToBookExcursion
from langgraph.graph import END


def route_primary_assistant(state: State) -> str:
    """
    Route from primary assistant to appropriate workflow entry points based on tool calls.
    
    This function implements the delegation layer of the routing system, analyzing
    tool calls from the primary assistant to determine which specialized workflow
    should handle the customer's request. It routes to entry points (enter_*) for
    first-time workflow delegation, ensuring proper workflow initialization.
    
    Routing Logic:
        - Analyzes the last message for tool calls
        - Maps delegation tools to appropriate workflow entry points
        - Provides fallbacks for general tools and conversation continuation
        - Handles conversation termination scenarios
    
    Tool Call Mapping:
        ToFlightBookingAssistant → enter_update_flight
        ToBookCarRental → enter_book_car_rental
        ToHotelBookingAssistant → enter_book_hotel
        ToBookExcursion → enter_book_excursion
        Other tools → primary_assistant_tools
    
    Args:
        state: Current conversation state containing message history
        
    Returns:
        String indicating the next node to execute:
        - "enter_*": Workflow entry points for delegation
        - "primary_assistant_tools": General tool execution
        - "primary_assistant": Continue with primary assistant
        - END: Terminate conversation
        
    Example:
        >>> state = {"messages": [HumanMessage(tool_calls=[{"name": "ToFlightBookingAssistant"}])]}
        >>> next_node = route_primary_assistant(state)
        >>> # Returns "enter_update_flight" for flight workflow delegation
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
    
    # Route to entry points for workflow delegation (original notebook pattern)
    if tool_name == ToFlightBookingAssistant.__name__:
        return "enter_update_flight"
    elif tool_name == ToBookCarRental.__name__:
        return "enter_book_car_rental"
    elif tool_name == ToHotelBookingAssistant.__name__:
        return "enter_book_hotel"
    elif tool_name == ToBookExcursion.__name__:
        return "enter_book_excursion"
    else:
        # Route to general tools for non-delegation tool calls
        return "primary_assistant_tools"


def route_to_workflow(state: State) -> Literal[
    "primary_assistant",
    "update_flight", 
    "book_car_rental",
    "book_hotel", 
    "book_excursion"
]:
    """
    Route user input to appropriate workflow assistant nodes for conversation continuation.
    
    This function implements the continuation layer of the routing system, directing
    user messages to the appropriate specialized assistant based on the current
    dialog state. Unlike route_primary_assistant, this routes directly to assistant
    nodes (not entry points) to maintain workflow context and conversation flow.
    
    Routing Strategy:
        - Uses dialog_state stack to determine active workflow
        - Routes to assistant nodes for workflow continuation
        - Fallback to primary assistant for new conversations
        - Supports all specialized workflow domains
    
    Dialog State Mapping:
        "update_flight" → update_flight (Flight Assistant)
        "book_car_rental" → book_car_rental (Car Rental Assistant)
        "book_hotel" → book_hotel (Hotel Assistant)
        "book_excursion" → book_excursion (Excursion Assistant)
        No state/unknown → primary_assistant
    
    Key Difference from route_primary_assistant:
        - This routes to assistant nodes directly (update_flight, book_car_rental, etc.)
        - route_primary_assistant routes to entry points (enter_update_flight, etc.)
        - This maintains workflow context; route_primary_assistant initiates workflows
    
    Args:
        state: Current conversation state with dialog_state stack
        
    Returns:
        Literal string indicating the assistant node to execute:
        - "primary_assistant": No active workflow or unknown state
        - "update_flight": Continue in flight workflow
        - "book_car_rental": Continue in car rental workflow
        - "book_hotel": Continue in hotel workflow
        - "book_excursion": Continue in excursion workflow
        
    Example:
        >>> state = {"dialog_state": ["assistant", "update_flight"], "messages": [...]}
        >>> next_node = route_to_workflow(state)
        >>> # Returns "update_flight" to continue in flight workflow
    """
    dialog_state = state.get("dialog_state", [])
    if not dialog_state:
        return "primary_assistant"
    
    # Get the current active workflow from the dialog state stack
    current_workflow = dialog_state[-1]
    
    # Route to appropriate assistant node based on workflow context
    supported_workflows = ["update_flight", "book_car_rental", "book_hotel", "book_excursion"]
    if current_workflow in supported_workflows:
        return current_workflow
    else:
        # Fallback to primary assistant for unknown or invalid workflows
        return "primary_assistant"


# === WORKFLOW-SPECIFIC ROUTING IMPORTS ===
# Import specialized routing functions from each workflow module
# These handle tool selection within each specialized workflow

# Flight workflow tool routing - determines safe vs. sensitive flight tools
from customer_support_agent.workflows.flight_workflow import route_update_flight

# Hotel workflow tool routing - determines safe vs. sensitive hotel tools
from customer_support_agent.workflows.hotel_workflow import route_book_hotel

# Car rental workflow tool routing - determines safe vs. sensitive rental tools
from customer_support_agent.workflows.car_rental_workflow import route_book_car_rental

# Excursion workflow tool routing - determines safe vs. sensitive excursion tools  
from customer_support_agent.workflows.excursion_workflow import route_book_excursion 
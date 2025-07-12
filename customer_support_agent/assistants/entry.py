"""
Entry Assistant Module - User Information Initialization

This module provides the entry point for customer support conversations by
fetching and initializing user context information. It serves as the first
step in every conversation, ensuring that subsequent interactions have access
to the customer's current flight bookings and profile information.

The entry node is responsible for:
    - Retrieving customer's current flight bookings and details
    - Initializing user context for personalized assistance
    - Providing foundation data for workflow routing decisions
    - Enabling context-aware responses from all assistants

This information becomes available to all subsequent assistants and tools,
allowing for personalized recommendations and informed decision-making
throughout the conversation.

Functions:
    user_info_node: Fetches and returns user flight information for context
"""

from customer_support_agent.state import State
from customer_support_agent.tools import fetch_user_flight_information


def user_info_node(state: State) -> State:
    """
    Initialize user context by fetching current flight information.
    
    This node serves as the entry point for all customer support conversations,
    retrieving the customer's current flight bookings, seat assignments, and
    related information to provide context for personalized assistance.
    
    The fetched information includes:
        - Current flight bookings and ticket details
        - Seat assignments and fare conditions
        - Booking references and flight schedules
        - Departure and arrival information
    
    This context enables all subsequent assistants to provide informed,
    personalized responses and make appropriate workflow routing decisions
    based on the customer's current travel situation.
    
    Args:
        state: Current conversation state (user_info will be populated)
        
    Returns:
        Updated state with user_info containing customer's flight details
        
    Example:
        >>> state = {"messages": [...], "user_info": "", "dialog_state": []}
        >>> updated_state = user_info_node(state)
        >>> # updated_state["user_info"] now contains flight information
    """
    return {"user_info": fetch_user_flight_information.invoke({})}


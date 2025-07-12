"""
State Management Module - Defines the application state structure for customer support workflows.

This module contains the core state definition that tracks conversation state,
user information, and dialog flow throughout the customer support interaction.
The state follows LangGraph patterns for multi-agent conversations with workflow routing.

Classes:
    State: TypedDict defining the complete application state structure
    
Functions:
    update_dialog_stack: Manages the dialog state stack for workflow transitions
"""

from typing import Annotated

from typing_extensions import TypedDict
from typing import Annotated, Literal, Optional
from langgraph.graph.message import AnyMessage, add_messages

def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """
    Manage the dialog state stack for workflow transitions.
    
    This function handles pushing new workflow states onto the stack or popping
    the current state when workflows complete. It's used to track which specialized
    assistant is currently handling the conversation.
    
    Args:
        left: Current dialog state stack
        right: New state to add, "pop" to remove last state, or None for no change
        
    Returns:
        Updated dialog state stack
        
    Examples:
        >>> update_dialog_stack(["assistant"], "update_flight")
        ["assistant", "update_flight"]
        >>> update_dialog_stack(["assistant", "update_flight"], "pop")
        ["assistant"]
        >>> update_dialog_stack(["assistant"], None)
        ["assistant"]
    """
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]

class State(TypedDict):
    """
    Application state structure for customer support conversations.
    
    This TypedDict defines the complete state that flows through the LangGraph
    workflow system, tracking messages, user context, and workflow routing state.
    
    Attributes:
        messages: Conversation history with automatic message aggregation
        user_info: Current user's flight and booking information as a string
        dialog_state: Stack tracking which specialized assistant is active
            - "assistant": Primary customer support assistant
            - "update_flight": Flight booking and modification workflow
            - "book_car_rental": Car rental booking workflow  
            - "book_hotel": Hotel booking workflow
            - "book_excursion": Trip recommendations and excursion booking workflow
    """
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    dialog_state: Annotated[
                    list[Literal[
                        "assistant", 
                        "update_flight",
                        "book_car_rental",
                        "book_hotel",
                        "book_excursion",
                        ]], 
            update_dialog_stack]

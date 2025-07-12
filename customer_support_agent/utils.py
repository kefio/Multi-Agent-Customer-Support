"""
Utilities Module - Shared utilities and helper functions for the customer support system.

This module provides reusable components for the LangGraph-based customer support AI,
including assistant wrappers, tool node creation, dialog state management, and 
database utilities. It supports the multi-workflow architecture by providing
common functionality used across different specialized assistants.

Classes:
    Assistant: Wrapper for creating reusable assistant nodes
    
Functions:
    pop_dialog_state: Manages dialog stack transitions
    create_entry_node: Factory for workflow entry points
    handle_tool_error: Error handling for tool execution
    create_tool_node_with_fallback: Creates resilient tool nodes
    update_dates: Updates database with current timestamps
    _print_event: Debug utility for conversation events
"""

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda, Runnable, RunnableConfig

from langgraph.prebuilt.tool_node import ToolNode

import shutil
import sqlite3

import pandas as pd
from typing import Callable

from customer_support_agent.state import State

# Database file paths
local_file = "travel2.sqlite"
backup_file = "travel2.backup.sqlite"

# === SHARED NODE UTILITIES FOR MULTI-WORKFLOW ARCHITECTURE ===

class Assistant:
    """
    Reusable assistant node wrapper for LangGraph workflows.
    
    This class creates a standardized assistant node that can be used consistently
    across the main graph and specialized workflows. It handles common patterns
    like empty response handling and ensures reliable assistant behavior.
    
    The assistant wrapper automatically retries when the LLM returns empty
    responses, ensuring consistent interaction quality.
    
    Attributes:
        runnable: The LangChain runnable (typically prompt | llm.bind_tools())
        
    Example:
        >>> from customer_support_agent.assistants.primary import primary_assistant_runnable
        >>> primary_assistant = Assistant(primary_assistant_runnable)
        >>> # Can now be used as a node in the graph
        >>> builder.add_node("primary_assistant", primary_assistant)
    """
    
    def __init__(self, runnable: Runnable):
        """
        Initialize the assistant with a LangChain runnable.
        
        Args:
            runnable: LangChain runnable that processes state and returns messages
        """
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        """
        Execute the assistant with automatic empty response handling.
        
        Invokes the underlying runnable and retries if empty responses are received.
        This ensures the assistant always provides meaningful output to continue
        the conversation flow.
        
        Args:
            state: Current conversation state
            config: Runtime configuration
            
        Returns:
            Dict with updated messages containing the assistant's response
        """
        while True:
            result = self.runnable.invoke(state)
            
            # Handle empty responses by prompting for actual output
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}
    
def pop_dialog_state(state: State) -> dict:
    """
    Pop the dialog stack and return control to the primary assistant.

    This function handles the transition from specialized workflow assistants
    back to the primary assistant. It manages the dialog state stack and 
    provides appropriate context messages for seamless conversation flow.
    
    Used when specialized assistants complete their tasks or need to escalate
    back to the primary assistant for handling requests outside their domain.

    Args:
        state: Current conversation state with dialog_state stack

    Returns:
        Dict containing:
        - dialog_state: "pop" signal to remove current workflow from stack
        - messages: Context message for primary assistant resumption (if needed)
        
    Example:
        >>> state = {"dialog_state": ["assistant", "update_flight"], "messages": [...]}
        >>> result = pop_dialog_state(state)
        >>> # Result enables transition back to primary assistant
    """
    messages = []
    
    # If the last message is a tool call, add a tool message to resume
    # conversation with the primary assistant
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="Resuming dialog with primary assistant. Please reflect on the past conversation and assist the user with their request.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"]
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages
    }

def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    """
    Factory function to create entry points for specialized workflow assistants.
    
    Generates standardized entry nodes that handle the transition from the primary
    assistant to specialized workflow assistants. Each entry node updates the
    dialog state and provides appropriate context for the specialized assistant.
    
    This factory pattern ensures consistent behavior across all workflow entry points
    while allowing customization for each specialized domain.

    Args:
        assistant_name: Human-readable name of the specialized assistant
        new_dialog_state: State identifier for the workflow (e.g., "update_flight")

    Returns:
        Callable entry node function that can be used in LangGraph
        
    Example:
        >>> flight_entry = create_entry_node("Flight Updates Assistant", "update_flight")
        >>> builder.add_node("enter_update_flight", flight_entry)
    """
    def entry_node(state: State) -> dict:
        """
        Entry point implementation for a specialized workflow assistant.
        
        Updates dialog state and provides context for the specialized assistant
        to take over the conversation from the primary assistant.
        
        Args:
            state: Current conversation state
            
        Returns:
            Dict with updated dialog_state and context message
        """
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "dialog_state": new_dialog_state,
            "messages": [
                ToolMessage(
                   content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, or other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id
                )
            ]
        }
    return entry_node

def handle_tool_error(state) -> dict:
    """
    Handle tool execution errors with informative error messages.
    
    Provides standardized error handling for tool failures, ensuring users
    receive helpful error information and guidance for resolution.
    
    Args:
        state: State containing error information and failed tool calls
        
    Returns:
        Dict with error messages for each failed tool call
    """
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\nPlease fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: list) -> ToolNode:
    """
    Create a ToolNode with error handling fallback capabilities.
    
    Builds resilient tool nodes using LangGraph's official implementation
    with automatic fallback to error handling when tool execution fails.
    
    This ensures the conversation can continue gracefully even when tools
    encounter errors, providing users with helpful error messages instead
    of system crashes.

    Args:
        tools: List of LangChain tools to include in the node

    Returns:
        ToolNode with fallback error handling
        
    Example:
        >>> safe_tools = [search_flights, lookup_policy]
        >>> safe_tools_node = create_tool_node_with_fallback(safe_tools)
        >>> builder.add_node("flight_safe_tools", safe_tools_node)
    """
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def _print_event(event: dict, _printed: set, max_length=1500):
    """
    Debug utility for printing conversation events during development.
    
    Formats and displays conversation events for debugging and monitoring
    the flow of multi-workflow conversations. Tracks printed messages to
    avoid duplicates and truncates long messages for readability.

    Args:
        event: LangGraph event containing conversation state
        _printed: Set of already printed message IDs to avoid duplicates  
        max_length: Maximum length for message display (default: 1500)
        
    Example:
        >>> _printed = set()
        >>> for event in graph.stream(inputs, config):
        ...     _print_event(event, _printed)
    """
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)


def update_dates(file):
    """
    Update database timestamps to current time for realistic demo data.
    
    Modifies the travel database to use current timestamps instead of
    historical data, making the demo experience more realistic and relevant.
    This ensures flight schedules and booking dates reflect recent times.
    
    The function:
    1. Restores database from backup
    2. Calculates time difference between sample data and current time
    3. Updates all datetime columns to current timeframe
    4. Commits changes to database
    
    Args:
        file: Path to the SQLite database file to update
        
    Returns:
        Path to the updated database file
        
    Example:
        >>> updated_db = update_dates("travel2.sqlite")
        >>> # Database now has current timestamps for realistic demo
    """
    # Restore from backup to ensure clean starting state
    shutil.copy(backup_file, file)
    conn = sqlite3.connect(file)
    cursor = conn.cursor()

    # Load all tables into pandas DataFrames for efficient processing
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table';", conn
    ).name.tolist()
    tdf = {}
    for t in tables:
        tdf[t] = pd.read_sql(f"SELECT * from {t}", conn)

    # Calculate time difference between sample data and current time
    example_time = pd.to_datetime(
        tdf["flights"]["actual_departure"].replace("\\N", pd.NaT)
    ).max()
    current_time = pd.to_datetime("now").tz_localize(example_time.tz)
    time_diff = current_time - example_time

    # Update booking dates to current timeframe
    tdf["bookings"]["book_date"] = (
        pd.to_datetime(tdf["bookings"]["book_date"].replace("\\N", pd.NaT), utc=True)
        + time_diff
    )

    # Update all flight datetime columns
    datetime_columns = [
        "scheduled_departure",
        "scheduled_arrival", 
        "actual_departure",
        "actual_arrival",
    ]
    for column in datetime_columns:
        tdf["flights"][column] = (
            pd.to_datetime(tdf["flights"][column].replace("\\N", pd.NaT)) + time_diff
        )

    # Write updated data back to database
    for table_name, df in tdf.items():
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    
    # Clean up memory and commit changes
    del df
    del tdf
    conn.commit()
    conn.close()

    return file
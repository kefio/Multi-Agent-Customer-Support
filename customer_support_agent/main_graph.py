"""
Main Graph Module - Central orchestrator for the Swiss Airlines Customer Support AI

This module implements the core LangGraph architecture that coordinates multiple
specialized workflow assistants for comprehensive customer support. Following the
original LangGraph tutorial pattern, all workflow nodes are integrated directly
into a single main graph without subgraphs, enabling seamless conversation flow
and state management across different domains.

Architecture Overview:
    - Primary Assistant: Handles general queries and delegates to specialists
    - Flight Workflow: Manages flight updates, cancellations, and rebookings
    - Hotel Workflow: Handles hotel search, booking, and modifications
    - Car Rental Workflow: Manages vehicle rental bookings and updates
    - Excursion Workflow: Processes trip recommendations and activity bookings

The graph uses conditional routing to direct conversations between assistants
based on user intent and maintains conversation state through a centralized
dialog stack. Human-in-the-loop capabilities ensure sensitive operations
require explicit approval before execution.

Functions:
    create_main_graph: Constructs the complete workflow graph
    compile_graph: Compiles graph with memory and interrupt capabilities
    
Variables:
    graph: Pre-compiled graph instance ready for immediate use
"""

from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

from customer_support_agent.state import State
from customer_support_agent.utils import Assistant, create_tool_node_with_fallback
from customer_support_agent.assistants.entry import user_info_node
from customer_support_agent.assistants.primary import primary_assistant_runnable, primary_assistant_tools
from customer_support_agent.routing import route_primary_assistant, route_to_workflow

# Import all specialized workflow components
from customer_support_agent.workflows import (
    # Flight workflow components - handles flight updates and cancellations
    flight_entry_node, flight_assistant_node, flight_safe_tools_node, 
    flight_sensitive_tools_node, flight_leave_node, route_update_flight,
    
    # Hotel workflow components - manages hotel bookings and modifications
    hotel_entry_node, hotel_assistant_node, hotel_safe_tools_node,
    hotel_sensitive_tools_node, hotel_leave_node, route_book_hotel,
    
    # Car rental workflow components - handles vehicle rental services  
    car_rental_entry_node, car_rental_assistant_node, car_rental_safe_tools_node, 
    car_rental_sensitive_tools_node, car_rental_leave_node, route_book_car_rental,
    
    # Excursion workflow components - processes trip recommendations and activities
    excursion_entry_node, excursion_assistant_node, excursion_safe_tools_node,
    excursion_sensitive_tools_node, excursion_leave_node, route_book_excursion,
)


def create_main_graph():
    """
    Construct the main LangGraph for multi-workflow customer support.
    
    Creates a comprehensive graph architecture that integrates all specialized
    workflow assistants into a single, cohesive conversation system. The graph
    follows a hub-and-spoke pattern where the primary assistant acts as the
    central coordinator, delegating to specialized assistants as needed.
    
    Graph Structure:
        1. User Information Fetching: Retrieves customer context
        2. Primary Assistant Hub: Handles general queries and delegation
        3. Specialized Workflow Nodes: Domain-specific assistance
        4. Tool Execution Nodes: Safe and sensitive operation handling
        5. Conditional Routing: Dynamic conversation flow management
    
    Node Categories:
        - Core Nodes: User info, primary assistant, and shared utilities
        - Entry Nodes: Workflow delegation entry points (enter_*)
        - Assistant Nodes: Specialized domain assistants (update_flight, etc.)
        - Tool Nodes: Safe and sensitive tool execution (*_tools)
        - Control Nodes: Workflow exit and state management (leave_skill)
    
    Edge Types:
        - Direct Edges: Fixed transitions between nodes
        - Conditional Edges: Dynamic routing based on conversation state
        - Tool Routing: Automatic transitions after tool execution
    
    Returns:
        StateGraph builder configured with all nodes and routing logic
        
    Example:
        >>> builder = create_main_graph()
        >>> graph = builder.compile(checkpointer=MemorySaver())
        >>> # Graph ready for conversation processing
    """
    builder = StateGraph(State)
    
    # === CORE SYSTEM NODES ===
    # These nodes handle the fundamental conversation infrastructure
    
    # Fetch user flight information and context for personalized assistance
    builder.add_node("fetch_user_info", user_info_node)
    
    # Primary assistant - central hub for general queries and workflow delegation
    builder.add_node("primary_assistant", Assistant(primary_assistant_runnable))
    
    # Primary assistant tools - handles general search and policy lookup
    builder.add_node("primary_assistant_tools", create_tool_node_with_fallback(primary_assistant_tools))
    
    # === SPECIALIZED WORKFLOW NODES ===
    # Each workflow includes entry, assistant, tools, and routing components
    
    # Flight Workflow - Comprehensive flight management capabilities
    builder.add_node("enter_update_flight", flight_entry_node)          # Entry point for flight delegation
    builder.add_node("update_flight", flight_assistant_node)            # Flight specialist assistant
    builder.add_node("update_flight_safe_tools", flight_safe_tools_node)     # Non-destructive flight operations
    builder.add_node("update_flight_sensitive_tools", flight_sensitive_tools_node)  # Flight modifications requiring approval
    
    # Hotel Workflow - Hotel booking and management services
    builder.add_node("enter_book_hotel", hotel_entry_node)              # Entry point for hotel delegation
    builder.add_node("book_hotel", hotel_assistant_node)                # Hotel specialist assistant
    builder.add_node("book_hotel_safe_tools", hotel_safe_tools_node)         # Hotel search and information
    builder.add_node("book_hotel_sensitive_tools", hotel_sensitive_tools_node)    # Hotel bookings requiring approval
    
    # Car Rental Workflow - Vehicle rental booking and modification services
    builder.add_node("enter_book_car_rental", car_rental_entry_node)    # Entry point for car rental delegation
    builder.add_node("book_car_rental", car_rental_assistant_node)      # Car rental specialist assistant
    builder.add_node("book_car_rental_safe_tools", car_rental_safe_tools_node)   # Vehicle search and information
    builder.add_node("book_car_rental_sensitive_tools", car_rental_sensitive_tools_node)  # Rental bookings requiring approval
    
    # Excursion Workflow - Trip recommendations and activity booking services
    builder.add_node("enter_book_excursion", excursion_entry_node)      # Entry point for excursion delegation
    builder.add_node("book_excursion", excursion_assistant_node)        # Excursion specialist assistant
    builder.add_node("book_excursion_safe_tools", excursion_safe_tools_node)     # Activity search and recommendations
    builder.add_node("book_excursion_sensitive_tools", excursion_sensitive_tools_node)   # Activity bookings requiring approval
    
    # Shared Control Node - Common exit point for all workflows
    builder.add_node("leave_skill", flight_leave_node)  # Returns control to primary assistant
    
    # === CORE CONVERSATION FLOW EDGES ===
    # Direct transitions for fundamental conversation infrastructure
    
    builder.add_edge(START, "fetch_user_info")                          # Always start with user context
    builder.add_edge("primary_assistant_tools", "primary_assistant")    # Return to primary after tool execution
    builder.add_edge("leave_skill", "primary_assistant")                # Return to primary when workflows complete
    
    # === WORKFLOW-SPECIFIC DIRECT EDGES ===
    # Fixed transitions within each specialized workflow
    
    # Flight Workflow Edges
    builder.add_edge("enter_update_flight", "update_flight")                    # Entry → Assistant
    builder.add_edge("update_flight_safe_tools", "update_flight")              # Safe Tools → Assistant
    builder.add_edge("update_flight_sensitive_tools", "update_flight")         # Sensitive Tools → Assistant
    
    # Hotel Workflow Edges  
    builder.add_edge("enter_book_hotel", "book_hotel")                          # Entry → Assistant
    builder.add_edge("book_hotel_safe_tools", "book_hotel")                    # Safe Tools → Assistant
    builder.add_edge("book_hotel_sensitive_tools", "book_hotel")               # Sensitive Tools → Assistant
    
    # Car Rental Workflow Edges
    builder.add_edge("enter_book_car_rental", "book_car_rental")                # Entry → Assistant
    builder.add_edge("book_car_rental_safe_tools", "book_car_rental")          # Safe Tools → Assistant
    builder.add_edge("book_car_rental_sensitive_tools", "book_car_rental")     # Sensitive Tools → Assistant
    
    # Excursion Workflow Edges
    builder.add_edge("enter_book_excursion", "book_excursion")                  # Entry → Assistant
    builder.add_edge("book_excursion_safe_tools", "book_excursion")            # Safe Tools → Assistant
    builder.add_edge("book_excursion_sensitive_tools", "book_excursion")       # Sensitive Tools → Assistant
    
    # === CONDITIONAL ROUTING EDGES ===
    # Dynamic conversation flow based on state and intent
    
    # Primary Assistant Routing - Delegates to appropriate workflows or tools
    # Routes based on tool calls from primary assistant to entry points
    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        [
            "enter_update_flight",      # Flight workflow delegation
            "enter_book_car_rental",    # Car rental workflow delegation
            "enter_book_hotel",         # Hotel workflow delegation
            "enter_book_excursion",     # Excursion workflow delegation
            "primary_assistant_tools",  # General tool usage
            "primary_assistant",        # Self-loop for continued conversation
            END,                        # Conversation termination
        ],
    )
    
    # User Input Routing - Directs continued conversations to appropriate assistants
    # Routes based on dialog state to maintain workflow context
    builder.add_conditional_edges(
        "fetch_user_info", 
        route_to_workflow,
        [
            "primary_assistant",        # No active workflow - use primary
            "update_flight",           # Continue in flight workflow
            "book_car_rental",         # Continue in car rental workflow
            "book_hotel",              # Continue in hotel workflow
            "book_excursion",          # Continue in excursion workflow
        ]
    )
    
    # Workflow-Specific Tool Routing - Determines appropriate tools for each assistant
    
    # Flight Assistant Tool Routing
    builder.add_conditional_edges(
        "update_flight",
        route_update_flight,
        ["update_flight_safe_tools", "update_flight_sensitive_tools", "leave_skill"]
    )
    
    # Hotel Assistant Tool Routing
    builder.add_conditional_edges(
        "book_hotel",
        route_book_hotel,
        ["book_hotel_safe_tools", "book_hotel_sensitive_tools", "leave_skill"]
    )
    
    # Car Rental Assistant Tool Routing
    builder.add_conditional_edges(
        "book_car_rental",
        route_book_car_rental,
        ["book_car_rental_safe_tools", "book_car_rental_sensitive_tools", "leave_skill"]
    )
    
    # Excursion Assistant Tool Routing
    builder.add_conditional_edges(
        "book_excursion",
        route_book_excursion,
        ["book_excursion_safe_tools", "book_excursion_sensitive_tools", "leave_skill"]
    )
    
    return builder


def compile_graph():
    """
    Compile the main graph with memory persistence and human-in-the-loop capabilities.
    
    Creates a production-ready graph instance with conversation memory and
    safety controls. The compiled graph includes checkpoint persistence for
    conversation continuity and interrupt points for sensitive operations
    requiring human approval.
    
    Features:
        - Memory Checkpointing: Maintains conversation state across interactions
        - Human-in-the-Loop: Pauses execution before sensitive operations
        - Error Recovery: Supports conversation resumption after interruptions
        - State Persistence: Enables conversation continuation across sessions
    
    Interrupt Points:
        All sensitive tool nodes are configured as interrupt points, requiring
        explicit human approval before executing operations that modify bookings,
        process payments, or perform other irreversible actions.
    
    Returns:
        Compiled LangGraph ready for conversation processing
        
    Example:
        >>> graph = compile_graph()
        >>> config = {"configurable": {"thread_id": "conversation-1"}}
        >>> response = graph.invoke({"messages": [("user", "Hi")]}, config)
    """
    builder = create_main_graph()
    memory_saver = MemorySaver()
    
    # Configure human-in-the-loop interrupt points for sensitive operations
    # These operations require explicit approval before execution
    interrupt_before = [
        "update_flight_sensitive_tools",      # Flight modifications and cancellations
        "book_car_rental_sensitive_tools",    # Car rental bookings and changes
        "book_hotel_sensitive_tools",         # Hotel bookings and modifications
        "book_excursion_sensitive_tools",     # Excursion bookings and changes
    ]
    
    return builder.compile(
        checkpointer=memory_saver,        # Enable conversation memory
        interrupt_before=interrupt_before  # Configure approval checkpoints
    )


# === GRAPH INSTANCE FOR IMMEDIATE USE ===
# Pre-compiled graph instance ready for deployment and testing
graph = compile_graph() 
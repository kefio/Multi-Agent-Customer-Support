"""
Workflows Package - Specialized Customer Support Workflow Implementations

This package contains modular workflow implementations for the Swiss Airlines
Customer Support AI system. Each workflow module provides specialized assistance
for specific domains while maintaining consistent architecture patterns and
seamless integration with the main graph.

Architecture Philosophy:
    This package replaces the previous subgraph approach with a more modular
    organization pattern. All nodes are still integrated directly into the main
    graph (following LangGraph best practices), but workflow-specific logic is
    organized into separate modules for maintainability and clarity.

Package Contents:
    - flight_workflow: Flight booking updates, cancellations, and modifications
    - hotel_workflow: Hotel search, booking, and accommodation management
    - car_rental_workflow: Vehicle rental booking and management services
    - excursion_workflow: Trip recommendations and activity booking services

Common Workflow Components:
    Each workflow module implements a consistent pattern of components:
    
    Entry Nodes: Handle delegation from primary assistant
        - Creates context for specialized assistant
        - Updates dialog state for workflow tracking
        - Provides seamless transition experience
    
    Assistant Nodes: Specialized domain assistants
        - Expert knowledge in specific domain
        - Context-aware conversation handling
        - Tool selection and execution management
    
    Tool Nodes: Categorized tool execution
        - Safe Tools: Information retrieval without side effects
        - Sensitive Tools: Operations requiring human approval
        - Error handling and fallback mechanisms
    
    Routing Functions: Intelligent tool and workflow routing
        - Determines appropriate tools based on assistant intent
        - Manages workflow completion and escalation
        - Provides fallback paths for edge cases
    
    Leave Nodes: Workflow completion and control transfer
        - Returns control to primary assistant
        - Maintains conversation context
        - Enables seamless workflow transitions

Integration Benefits:
    - Modular code organization without subgraph complexity
    - Consistent patterns across all specialized domains
    - Easy testing and maintenance of individual workflows
    - Scalable architecture for adding new service domains
    - Preserved conversation context across workflow transitions

Usage Example:
    All workflows are automatically integrated into the main graph:
    
    >>> from customer_support_agent.main_graph import graph
    >>> # All workflow nodes are available in the compiled graph
    >>> response = graph.invoke({"messages": [("user", "I need to change my flight")]})
    >>> # Automatically routes to flight workflow based on intent
"""

# Import all workflow components for main graph integration
from .flight_workflow import *
from .hotel_workflow import *
from .car_rental_workflow import *
from .excursion_workflow import *

# Export all workflow components for easy access by main graph
__all__ = [
    # === FLIGHT WORKFLOW COMPONENTS ===
    # Complete flight management workflow with entry, assistant, tools, and routing
    "flight_entry_node",            # Entry point for flight workflow delegation
    "flight_assistant_node",        # Specialized flight management assistant
    "flight_safe_tools_node",       # Non-destructive flight information tools
    "flight_sensitive_tools_node",  # Flight modification tools requiring approval
    "flight_leave_node",            # Workflow completion and control transfer
    "route_update_flight",          # Intelligent routing for flight operations
    
    # === HOTEL WORKFLOW COMPONENTS ===
    # Complete hotel booking workflow with search, booking, and management capabilities
    "hotel_entry_node",             # Entry point for hotel workflow delegation
    "hotel_assistant_node",         # Specialized hotel booking assistant
    "hotel_safe_tools_node",        # Hotel search and information tools
    "hotel_sensitive_tools_node",   # Hotel booking tools requiring approval
    "hotel_leave_node",             # Workflow completion and control transfer
    "route_book_hotel",             # Intelligent routing for hotel operations
    
    # === CAR RENTAL WORKFLOW COMPONENTS ===
    # Complete car rental workflow with search, booking, and management capabilities
    "car_rental_entry_node",        # Entry point for car rental workflow delegation
    "car_rental_assistant_node",    # Specialized car rental assistant
    "car_rental_safe_tools_node",   # Vehicle search and information tools
    "car_rental_sensitive_tools_node",  # Rental booking tools requiring approval
    "car_rental_leave_node",        # Workflow completion and control transfer
    "route_book_car_rental",        # Intelligent routing for car rental operations
    
    # === EXCURSION WORKFLOW COMPONENTS ===
    # Complete excursion workflow with recommendations, booking, and activity management
    "excursion_entry_node",         # Entry point for excursion workflow delegation
    "excursion_assistant_node",     # Specialized excursion and activity assistant
    "excursion_safe_tools_node",    # Activity search and recommendation tools
    "excursion_sensitive_tools_node",   # Excursion booking tools requiring approval
    "excursion_leave_node",         # Workflow completion and control transfer
    "route_book_excursion",         # Intelligent routing for excursion operations
] 
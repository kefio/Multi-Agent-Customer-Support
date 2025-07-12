"""
Main Graph - Clean implementation following the original LangGraph notebook pattern.

This module creates the main graph with all nodes directly in the graph 
(no subgraphs), following the exact structure from the tutorial.

All workflow-specific logic is imported from the workflows/ modules,
but nodes are added directly to this main graph.
"""

from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

from customer_support_agent.state import State
from customer_support_agent.utils import Assistant, create_tool_node_with_fallback
from customer_support_agent.assistants.entry import user_info_node
from customer_support_agent.assistants.primary import primary_assistant_runnable, primary_assistant_tools
from customer_support_agent.routing import route_primary_assistant, route_to_workflow

# Import workflow nodes - ALL WORKFLOWS IMPLEMENTED STEP 3
from customer_support_agent.workflows import (
    # Flight workflow - IMPLEMENTED STEP 2
    flight_entry_node, flight_assistant_node, flight_safe_tools_node, 
    flight_sensitive_tools_node, flight_leave_node, route_update_flight,
    
    # Hotel workflow - IMPLEMENTED STEP 3
    hotel_entry_node, hotel_assistant_node, hotel_safe_tools_node,
    hotel_sensitive_tools_node, hotel_leave_node, route_book_hotel,
    
    # Car rental workflow - IMPLEMENTED STEP 3
    car_rental_entry_node, car_rental_assistant_node, car_rental_safe_tools_node, 
    car_rental_sensitive_tools_node, car_rental_leave_node, route_book_car_rental,
    
    # Excursion workflow - IMPLEMENTED STEP 3
    excursion_entry_node, excursion_assistant_node, excursion_safe_tools_node,
    excursion_sensitive_tools_node, excursion_leave_node, route_book_excursion,
)


def create_main_graph():
    """
    Create the main graph following the original notebook pattern.
    
    Structure:
    1. User info node
    2. Primary assistant + tools
    3. All workflow nodes directly in main graph (no subgraphs!)
    4. Proper routing between entry points and assistant nodes
    """
    
    builder = StateGraph(State)
    
    # === CORE NODES ===
    builder.add_node("fetch_user_info", user_info_node)
    builder.add_node("primary_assistant", Assistant(primary_assistant_runnable))
    builder.add_node("primary_assistant_tools", create_tool_node_with_fallback(primary_assistant_tools))
    
    # === WORKFLOW NODES ===
    
    # Flight workflow nodes - STEP 2: IMPLEMENTED
    builder.add_node("enter_update_flight", flight_entry_node)
    builder.add_node("update_flight", flight_assistant_node)
    builder.add_node("update_flight_safe_tools", flight_safe_tools_node)
    builder.add_node("update_flight_sensitive_tools", flight_sensitive_tools_node)
    builder.add_node("leave_skill", flight_leave_node)  # Shared leave node
    
    # Hotel workflow nodes - IMPLEMENTED STEP 3
    builder.add_node("enter_book_hotel", hotel_entry_node)
    builder.add_node("book_hotel", hotel_assistant_node)
    builder.add_node("book_hotel_safe_tools", hotel_safe_tools_node)
    builder.add_node("book_hotel_sensitive_tools", hotel_sensitive_tools_node)
    
    # Car rental workflow nodes - IMPLEMENTED STEP 3
    builder.add_node("enter_book_car_rental", car_rental_entry_node)
    builder.add_node("book_car_rental", car_rental_assistant_node)
    builder.add_node("book_car_rental_safe_tools", car_rental_safe_tools_node)
    builder.add_node("book_car_rental_sensitive_tools", car_rental_sensitive_tools_node)
    
    # Excursion workflow nodes - IMPLEMENTED STEP 3
    builder.add_node("enter_book_excursion", excursion_entry_node)
    builder.add_node("book_excursion", excursion_assistant_node)
    builder.add_node("book_excursion_safe_tools", excursion_safe_tools_node)
    builder.add_node("book_excursion_sensitive_tools", excursion_sensitive_tools_node)
    
    # === CORE EDGES ===
    builder.add_edge(START, "fetch_user_info")
    builder.add_edge("primary_assistant_tools", "primary_assistant")
    
    # === WORKFLOW EDGES ===
    
    # Flight workflow edges - STEP 2: IMPLEMENTED
    builder.add_edge("enter_update_flight", "update_flight")
    builder.add_edge("update_flight_safe_tools", "update_flight")
    builder.add_edge("update_flight_sensitive_tools", "update_flight")
    builder.add_edge("leave_skill", "primary_assistant")
    
    # Hotel workflow edges - STEP 3: IMPLEMENTED
    builder.add_edge("enter_book_hotel", "book_hotel")
    builder.add_edge("book_hotel_safe_tools", "book_hotel")
    builder.add_edge("book_hotel_sensitive_tools", "book_hotel")
    
    # Car rental workflow edges - STEP 3: IMPLEMENTED
    builder.add_edge("enter_book_car_rental", "book_car_rental")
    builder.add_edge("book_car_rental_safe_tools", "book_car_rental")
    builder.add_edge("book_car_rental_sensitive_tools", "book_car_rental")
    
    # Excursion workflow edges - STEP 3: IMPLEMENTED
    builder.add_edge("enter_book_excursion", "book_excursion")
    builder.add_edge("book_excursion_safe_tools", "book_excursion")
    builder.add_edge("book_excursion_sensitive_tools", "book_excursion")
    
    # === CONDITIONAL EDGES ===
    # Main routing from primary assistant to entry points
    # ALL WORKFLOWS IMPLEMENTED STEP 3
    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        [
            "enter_update_flight",
            "enter_book_car_rental", 
            "enter_book_hotel",
            "enter_book_excursion",
            "primary_assistant_tools",
            "primary_assistant",  # Fallback for edge cases
            END,
        ],
    )
    
    # User input routing to appropriate workflow assistants
    # ALL WORKFLOWS IMPLEMENTED STEP 3
    builder.add_conditional_edges(
        "fetch_user_info", 
        route_to_workflow,
        [
            "primary_assistant",
            "update_flight",
            "book_car_rental", 
            "book_hotel",
            "book_excursion",
        ]
    )
    
    # Flight workflow conditional edges - STEP 2: IMPLEMENTED
    builder.add_conditional_edges(
        "update_flight",
        route_update_flight,
        ["update_flight_safe_tools", "update_flight_sensitive_tools", "leave_skill"]
    )
    
    # Hotel workflow conditional edges - STEP 3: IMPLEMENTED
    builder.add_conditional_edges(
        "book_hotel",
        route_book_hotel,
        ["book_hotel_safe_tools", "book_hotel_sensitive_tools", "leave_skill"]
    )
    
    # Car rental workflow conditional edges - STEP 3: IMPLEMENTED
    builder.add_conditional_edges(
        "book_car_rental",
        route_book_car_rental,
        ["book_car_rental_safe_tools", "book_car_rental_sensitive_tools", "leave_skill"]
    )
    
    # Excursion workflow conditional edges - STEP 3: IMPLEMENTED
    builder.add_conditional_edges(
        "book_excursion",
        route_book_excursion,
        ["book_excursion_safe_tools", "book_excursion_sensitive_tools", "leave_skill"]
    )
    
    return builder


def compile_graph():
    """Compile the main graph with memory checkpoint."""
    builder = create_main_graph()
    memory_saver = MemorySaver()
    
    # ALL WORKFLOWS: Add interrupt_before for all sensitive tools
    interrupt_before = [
        "update_flight_sensitive_tools",
        "book_car_rental_sensitive_tools", 
        "book_hotel_sensitive_tools",
        "book_excursion_sensitive_tools",
    ]
    
    return builder.compile(checkpointer=memory_saver, interrupt_before=interrupt_before)


# Compile and export the graph for immediate use
graph = compile_graph() 
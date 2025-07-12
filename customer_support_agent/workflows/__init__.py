"""
Workflows module - Contains domain-specific workflow definitions.

Each workflow module contains:
- Workflow-specific nodes
- Routing functions
- Tool configurations
- Assistant runnables

This replaces the previous subgraph approach with a more modular
organization while keeping all nodes in the main graph.
"""

from .flight_workflow import *
from .hotel_workflow import *
from .car_rental_workflow import *
from .excursion_workflow import *

__all__ = [
    # Flight workflow - IMPLEMENTED STEP 2
    "flight_entry_node", "flight_assistant_node", "flight_safe_tools_node", 
    "flight_sensitive_tools_node", "flight_leave_node", "route_update_flight",
    
    # Hotel workflow - IMPLEMENTED STEP 3
    "hotel_entry_node", "hotel_assistant_node", "hotel_safe_tools_node",
    "hotel_sensitive_tools_node", "hotel_leave_node", "route_book_hotel",
    
    # Car rental workflow - IMPLEMENTED STEP 3
    "car_rental_entry_node", "car_rental_assistant_node", "car_rental_safe_tools_node", 
    "car_rental_sensitive_tools_node", "car_rental_leave_node", "route_book_car_rental",
    
    # Excursion workflow - IMPLEMENTED STEP 3
    "excursion_entry_node", "excursion_assistant_node", "excursion_safe_tools_node",
    "excursion_sensitive_tools_node", "excursion_leave_node", "route_book_excursion",
] 
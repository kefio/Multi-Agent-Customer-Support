"""
Flight Assistant Module - Specialized Flight Management Assistant

This module implements a specialized assistant for handling all flight-related
customer requests including flight updates, cancellations, rebooking, and
schedule modifications. The assistant is specifically trained to work within
Swiss Airlines' policies and booking systems.

Key Capabilities:
    - Flight search and availability checking
    - Flight schedule updates and modifications
    - Ticket cancellations and refund processing
    - Policy compliance and fee calculation
    - Customer communication and confirmation

The flight assistant operates with both safe tools (information retrieval)
and sensitive tools (booking modifications) that require human approval
before execution. It maintains context awareness of the customer's current
bookings and provides policy-compliant recommendations.

Safety Features:
    - Policy consultation before making changes
    - Business rule enforcement (e.g., 3-hour minimum lead time)
    - Human approval required for sensitive operations
    - Comprehensive error handling and user feedback

Components:
    - flight_booking_prompt: Specialized prompt for flight operations
    - update_flight_safe_tools: Non-destructive information tools
    - update_flight_sensitive_tools: Booking modification tools requiring approval
    - update_flight_runnable: Complete executable flight assistant chain
"""

from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from customer_support_agent.tools import search_flights, update_ticket_to_new_flight, cancel_ticket, CompleteOrEscalate
from langchain_openai import ChatOpenAI

# Language model optimized for flight operations
llm = ChatOpenAI(model="gpt-4o")

# === FLIGHT ASSISTANT PROMPT TEMPLATE ===
# Specialized prompt designed for flight booking operations and customer service
flight_booking_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for handling flight updates and modifications. "
            "The primary assistant delegates flight-related work to you whenever customers need help updating their bookings. "
            
            # Core responsibilities and approach
            "Confirm the updated flight details with the customer and inform them of any additional fees. "
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "If you need more information or the customer changes their mind, escalate the task back to the main assistant. "
            "Remember that a booking isn't completed until after the relevant tool has successfully been used. "
            
            # Customer context for personalized service
            "\n\nCurrent user flight information:\n<Flights>\n{user_info}\n</Flights>"
            "\nCurrent time: {time}."
            
            # Escalation guidelines for scope management
            "\n\nIf the user needs help, and none of your tools are appropriate for it, then "
            '"CompleteOrEscalate" the dialog to the host assistant. Do not waste the user\'s time. '
            "Do not make up invalid tools or functions.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

# === TOOL CONFIGURATION ===
# Categorized tools for safe information retrieval vs. sensitive booking operations

# Safe Tools - Information retrieval and search operations
# These tools can be used without human approval as they don't modify bookings
update_flight_safe_tools = [search_flights]

# Sensitive Tools - Booking modifications requiring human approval
# These tools modify customer bookings and require explicit approval before execution
update_flight_sensitive_tools = [update_ticket_to_new_flight, cancel_ticket]

# === COMPLETE FLIGHT ASSISTANT CHAIN ===
# Combines specialized prompt, language model, and all flight-related tools
# Includes the CompleteOrEscalate tool for workflow management
update_flight_runnable = flight_booking_prompt | llm.bind_tools(
    update_flight_safe_tools + update_flight_sensitive_tools + [CompleteOrEscalate]
)
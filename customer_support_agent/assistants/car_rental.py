"""
Car Rental Assistant Module - Specialized Vehicle Rental Management Assistant

This module implements a specialized assistant for handling all car rental-related
customer requests including vehicle search, booking, modifications, and cancellations.
The assistant is designed to provide comprehensive car rental services with
knowledge of vehicle types, rental locations, and pricing tiers.

Key Capabilities:
    - Car rental search and availability checking across multiple locations
    - Vehicle booking and reservation management
    - Rental period modifications and extensions
    - Cancellation processing and refund handling
    - Customer preference matching and recommendations

The car rental assistant operates with safe tools for information gathering
and sensitive tools for booking operations that require human approval.
It provides detailed vehicle information and ensures customers understand
all rental terms and conditions.

Safety Features:
    - Human approval required for all booking operations
    - Comprehensive vehicle information and pricing transparency
    - Flexible search and filtering options
    - Clear escalation path for complex requests

Components:
    - book_car_rental_prompt: Specialized prompt for car rental operations
    - book_car_rental_safe_tools: Vehicle search and information tools
    - book_car_rental_sensitive_tools: Booking modification tools requiring approval
    - book_car_rental_runnable: Complete executable car rental assistant chain
"""

from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from customer_support_agent.tools import search_car_rentals, book_car_rental, update_car_rental, cancel_car_rental, CompleteOrEscalate
from langchain_openai import ChatOpenAI

# Language model optimized for car rental operations
llm = ChatOpenAI(model="gpt-4o")

# === CAR RENTAL ASSISTANT PROMPT TEMPLATE ===
# Specialized prompt designed for car rental operations and customer service
book_car_rental_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for handling car rental bookings and management. "
            "The primary assistant delegates car rental work to you whenever customers need help booking a vehicle. "
            
            # Core responsibilities and service approach
            "Search for available car rentals based on the user's preferences and confirm the booking details with the customer. "
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "If you need more information or the customer changes their mind, escalate the task back to the main assistant. "
            "Remember that a booking isn't completed until after the relevant tool has successfully been used. "
            
            # Time context for accurate availability
            "\nCurrent time: {time}."
            
            # Escalation guidelines and scope management  
            "\n\nIf the user needs help, and none of your tools are appropriate for it, then "
            '"CompleteOrEscalate" the dialog to the host assistant. Do not waste the user\'s time. '
            "Do not make up invalid tools or functions."
            
            # Example scenarios for escalation
            "\n\nSome examples for which you should CompleteOrEscalate:\n"
            " - 'what's the weather like this time of year?'\n"
            " - 'What flights are available?'\n"
            " - 'nevermind i think I'll book separately'\n"
            " - 'Oh wait i haven't booked my flight yet i'll do that first'\n"
            " - 'Car rental booking confirmed'",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

# === TOOL CONFIGURATION ===
# Categorized tools for safe information retrieval vs. sensitive booking operations

# Safe Tools - Vehicle search and information retrieval
# These tools provide information without making any booking commitments
book_car_rental_safe_tools = [search_car_rentals]

# Sensitive Tools - Booking operations requiring human approval
# These tools create, modify, or cancel actual rental bookings
book_car_rental_sensitive_tools = [
    book_car_rental,      # Create new car rental booking
    update_car_rental,    # Modify existing rental dates or details
    cancel_car_rental,    # Cancel existing rental booking
]

# === COMPLETE CAR RENTAL ASSISTANT CHAIN ===
# Combines specialized prompt, language model, and all car rental tools
# Includes workflow management capabilities for seamless delegation
book_car_rental_runnable = book_car_rental_prompt | llm.bind_tools(
    book_car_rental_safe_tools + book_car_rental_sensitive_tools + [CompleteOrEscalate]
)
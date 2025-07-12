"""
Hotel Assistant Module - Specialized Hotel Booking Management Assistant

This module implements a specialized assistant for handling all hotel-related
customer requests including accommodation search, booking, modifications, and
cancellations. The assistant provides comprehensive hotel services with
knowledge of different price tiers, locations, and amenities.

Key Capabilities:
    - Hotel search across multiple locations and price ranges
    - Accommodation booking and reservation management
    - Stay period modifications and room changes
    - Cancellation processing and policy application
    - Personalized recommendations based on customer preferences

The hotel assistant operates with safe tools for information gathering
and sensitive tools for booking operations that require human approval.
It helps customers find suitable accommodations while ensuring they
understand all booking terms and conditions.

Safety Features:
    - Human approval required for all booking operations
    - Comprehensive accommodation information and pricing transparency
    - Flexible search options across price tiers (Midscale to Luxury)
    - Clear escalation path for requests outside hotel booking scope

Components:
    - book_hotel_prompt: Specialized prompt for hotel operations
    - safe_tools: Hotel search and information retrieval tools
    - sensitive_tools: Booking modification tools requiring approval
    - book_hotel_runnable: Complete executable hotel assistant chain
"""

from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from customer_support_agent.tools import search_hotels, book_hotel, cancel_hotel, CompleteOrEscalate
from langchain_openai import ChatOpenAI

# Language model optimized for hotel booking operations
llm = ChatOpenAI(model="gpt-4o")

# === HOTEL ASSISTANT PROMPT TEMPLATE ===
# Specialized prompt designed for hotel booking operations and customer service
book_hotel_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for handling hotel bookings and accommodation management. "
            "The primary assistant delegates hotel-related work to you whenever customers need help booking accommodation. "
            
            # Core responsibilities and service approach
            "Search for available hotels based on the user's preferences and confirm the booking details with the customer. "
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "If you need more information or the customer changes their mind, escalate the task back to the main assistant. "
            "Remember that a booking isn't completed until after the relevant tool has successfully been used. "
            
            # Time context for accurate availability
            "\nCurrent time: {time}."
            
            # Escalation guidelines and scope management
            '\n\nIf the user needs help, and none of your tools are appropriate for it, then "CompleteOrEscalate" the dialog to the host assistant. '
            "Do not waste the user's time. Do not make up invalid tools or functions."
            
            # Example scenarios for escalation
            "\n\nSome examples for which you should CompleteOrEscalate:\n"
            " - 'what's the weather like this time of year?'\n"
            " - 'nevermind i think I'll book separately'\n"
            " - 'i need to figure out transportation while i'm there'\n"
            " - 'Oh wait i haven't booked my flight yet i'll do that first'\n"
            " - 'Hotel booking confirmed'",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

# === TOOL CONFIGURATION ===
# Categorized tools for safe information retrieval vs. sensitive booking operations

# Safe Tools - Hotel search and information retrieval
# These tools provide information without making any booking commitments
safe_tools = [search_hotels]

# Sensitive Tools - Booking operations requiring human approval
# These tools create or cancel actual hotel bookings
sensitive_tools = [book_hotel, cancel_hotel]

# === COMPLETE HOTEL ASSISTANT CHAIN ===
# Combines specialized prompt, language model, and all hotel-related tools
# Includes workflow management capabilities for seamless delegation
book_hotel_runnable = book_hotel_prompt | llm.bind_tools(
    safe_tools + sensitive_tools + [CompleteOrEscalate]
)
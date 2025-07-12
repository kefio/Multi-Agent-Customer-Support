"""
Excursion Assistant Module - Specialized Trip Recommendations and Activity Booking Assistant

This module implements a specialized assistant for handling all trip recommendation
and excursion-related customer requests including activity search, booking,
modifications, and cancellations. The assistant provides comprehensive travel
guidance with knowledge of local attractions, tours, and experiences.

Key Capabilities:
    - Trip recommendation search based on location and interests
    - Activity and excursion booking management
    - Tour modifications and special requirement handling
    - Cancellation processing and refund management
    - Personalized recommendations based on customer preferences and keywords

The excursion assistant operates with safe tools for information gathering
and sensitive tools for booking operations that require human approval.
It helps customers discover and book memorable experiences while ensuring
they understand all tour terms and conditions.

Safety Features:
    - Human approval required for all booking operations
    - Comprehensive activity information and pricing transparency
    - Flexible search with keyword-based content matching
    - Clear escalation path for requests outside excursion booking scope

Components:
    - book_excursion_prompt: Specialized prompt for excursion operations
    - book_excursion_safe_tools: Activity search and information tools
    - book_excursion_sensitive_tools: Booking modification tools requiring approval
    - book_excursion_runnable: Complete executable excursion assistant chain
"""

from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from customer_support_agent.tools import search_trip_recommendations, book_excursion, update_excursion, cancel_excursion, CompleteOrEscalate
from langchain_openai import ChatOpenAI

# Language model optimized for excursion and trip recommendation operations
llm = ChatOpenAI(model="gpt-4o")

# === EXCURSION ASSISTANT PROMPT TEMPLATE ===
# Specialized prompt designed for trip recommendation and excursion booking operations
book_excursion_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for handling trip recommendations and excursion bookings. "
            "The primary assistant delegates excursion work to you whenever customers need help booking recommended trips or activities. "
            
            # Core responsibilities and service approach
            "Search for available trip recommendations based on the user's preferences and confirm the booking details with the customer. "
            "If you need more information or the customer changes their mind, escalate the task back to the main assistant. "
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "Remember that a booking isn't completed until after the relevant tool has successfully been used. "
            
            # Time context for accurate availability
            "\nCurrent time: {time}."
            
            # Escalation guidelines and scope management
            '\n\nIf the user needs help, and none of your tools are appropriate for it, then "CompleteOrEscalate" the dialog to the host assistant. '
            "Do not waste the user's time. Do not make up invalid tools or functions."
            
            # Example scenarios for escalation
            "\n\nSome examples for which you should CompleteOrEscalate:\n"
            " - 'nevermind i think I'll book separately'\n"
            " - 'i need to figure out transportation while i'm there'\n"
            " - 'Oh wait i haven't booked my flight yet i'll do that first'\n"
            " - 'Excursion booking confirmed!'",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

# === TOOL CONFIGURATION ===
# Categorized tools for safe information retrieval vs. sensitive booking operations

# Safe Tools - Trip recommendation search and information retrieval
# These tools provide information without making any booking commitments
book_excursion_safe_tools = [search_trip_recommendations]

# Sensitive Tools - Booking operations requiring human approval
# These tools create, modify, or cancel actual excursion bookings
book_excursion_sensitive_tools = [book_excursion, update_excursion, cancel_excursion]

# === COMPLETE EXCURSION ASSISTANT CHAIN ===
# Combines specialized prompt, language model, and all excursion-related tools
# Includes workflow management capabilities for seamless delegation
book_excursion_runnable = book_excursion_prompt | llm.bind_tools(
    book_excursion_safe_tools + book_excursion_sensitive_tools + [CompleteOrEscalate]
)

"""
Primary Assistant Module - Central Customer Support AI Coordinator

This module implements the primary customer support assistant for Swiss Airlines,
serving as the central hub for all customer interactions. The primary assistant
handles general inquiries, performs initial customer service tasks, and delegates
specialized requests to domain-specific workflow assistants.

Key Responsibilities:
    - Flight information retrieval and policy consultation
    - Customer query analysis and intent recognition
    - Workflow delegation to specialized assistants
    - General customer support and guidance

The assistant is designed to be persistent in searching for information,
expanding query bounds when initial searches return no results, and
providing comprehensive assistance while maintaining context throughout
multi-turn conversations.

Components:
    - primary_assistant_prompt: Core conversation template with context
    - primary_assistant_tools: Available tools for direct use
    - primary_assistant_router_tools: Delegation tools for specialized workflows
    - primary_assistant_runnable: Complete executable assistant chain
"""

from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from customer_support_agent.tools import *

# === MODEL CONFIGURATION ===
# Language model selection and configuration for optimal performance

# Alternative model options for different performance/cost trade-offs:
# Haiku is faster and cheaper, but less accurate
# llm = ChatAnthropic(model="claude-3-haiku-20240307")
# llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=1)

# Note: When swapping LLMs, prompt optimization may be required for best results
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4-turbo-preview")

# === PRIMARY ASSISTANT PROMPT TEMPLATE ===
# Comprehensive prompt defining the assistant's role, capabilities, and behavior
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for Swiss Airlines. "
            "Your primary role is to search for flight information and company policies to answer customer queries. "
            
            # Delegation instructions for specialized workflows
            "If a customer requests to update or cancel a flight, book a car rental, book a hotel, or get trip recommendations, "
            "delegate the task to the appropriate specialized assistant by invoking the corresponding tool. "
            "You are not able to make these types of changes yourself. "
            "Only the specialized assistants are given permission to do this for the user. "
            
            # Transparency and user experience guidelines
            "The user is not aware of the different specialized assistants, so do not mention them; "
            "just quietly delegate through function calls. "
            
            # Information accuracy and persistence requirements
            "Provide detailed information to the customer, and always double-check the database before "
            "concluding that information is unavailable. "
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "If a search comes up empty, expand your search before giving up. "
            
            # Context injection for personalized assistance
            "\n\nCurrent user flight information:\n<Flights>\n{user_info}\n</Flights>"
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

# === TOOL CONFIGURATION ===
# Tools available directly to the primary assistant for immediate use

# Direct action tools - can be used immediately without delegation
primary_assistant_tools = [
    TavilySearch(max_results=1),        # Web search for real-time information
    fetch_user_flight_information,      # Retrieve customer's current bookings
    lookup_policy,                      # Company policy and guideline consultation
    search_flights,                     # Flight search and availability checking
]

# Delegation tools - route to specialized workflow assistants
primary_assistant_router_tools = [
    ToFlightBookingAssistant,           # Flight updates and cancellations
    ToBookCarRental,                    # Car rental bookings and management
    ToHotelBookingAssistant,            # Hotel bookings and modifications
    ToBookExcursion,                    # Trip recommendations and excursion bookings
]

# === COMPLETE ASSISTANT CHAIN ===
# Combines prompt template, language model, and all available tools
# This creates the complete executable assistant ready for conversation
primary_assistant_runnable = primary_assistant_prompt | llm.bind_tools(
    primary_assistant_tools + primary_assistant_router_tools
)
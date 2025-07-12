"""
Swiss Airlines Customer Support AI - Streamlit Web Interface

This module provides a user-friendly web interface for the Swiss Airlines Customer Support AI
system using Streamlit. The application offers an interactive chat interface with setup
management, conversation history, and human-in-the-loop approval for sensitive operations.

Features:
    - Interactive chat interface for customer support conversations
    - Automatic setup management for database and vector store initialization
    - Human approval workflow for sensitive booking operations
    - Conversation history and thread management
    - Real-time status monitoring and error handling
    - Multi-language support preparation

The interface handles the complete user journey from initial setup through complex
multi-workflow conversations, providing a seamless experience for both customers
and support representatives.
"""

import streamlit as st
import uuid
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage

# Load environment variables for API keys and configuration
load_dotenv()

from customer_support_agent.main_graph import graph
from customer_support_agent.utils import update_dates, local_file
from customer_support_agent.setup import (
    check_setup_complete, 
    get_setup_status, 
    run_full_setup,
    download_database,
    initialize_vector_store
)

# === STREAMLIT CONFIGURATION ===
# Configure the Streamlit page with appropriate metadata and layout
st.set_page_config(
    page_title="Customer Support AI",
    page_icon="✈️",
    layout="wide"
)

# === SESSION STATE INITIALIZATION ===
# Initialize all required session state variables for conversation management

# Conversation history - stores all messages in the current session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Unique thread identifier for conversation persistence and memory management
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Human approval workflow state - tracks when user approval is required
if "waiting_for_approval" not in st.session_state:
    st.session_state.waiting_for_approval = False

# Stores the event that triggered the approval request
if "pending_event" not in st.session_state:
    st.session_state.pending_event = None

# System setup completion status
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = check_setup_complete()

# Check current setup status for component availability
setup_status = get_setup_status()

# === SIDEBAR CONFIGURATION ===
# Create sidebar interface for user configuration and session management

st.sidebar.title("Configuration")

# Passenger ID input for personalized flight information retrieval
passenger_id = st.sidebar.text_input(
    "Passenger ID", 
    value="3442 587242",
    help="Passenger ID to retrieve flight information and booking details"
)

# New conversation button - resets all session state for fresh start
if st.sidebar.button("New Conversation"):
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.waiting_for_approval = False
    st.session_state.pending_event = None
    st.rerun()

# === MAIN INTERFACE ===
# Main application title and description
st.title("🛫 Customer Support AI")
st.markdown("AI Assistant for flight, hotel, car rental, and excursion bookings")

# === SETUP MANAGEMENT INTERFACE ===
# Display setup interface if system components are not ready
if not setup_status["setup_complete"]:
    # Setup required warning
    st.warning("⚠️ Initial Setup Required")
    st.markdown("Before using the assistant, you need to download the database and initialize the vector store.")
    
    # Display current component status
    col1, col2 = st.columns(2)
    
    with col1:
        if setup_status["database_exists"]:
            st.success("✅ Database already downloaded")
        else:
            st.error("❌ Database not found")
    
    with col2:
        if setup_status["vector_store_exists"]:
            st.success("✅ Vector store already initialized")
        else:
            st.error("❌ Vector store not found")
    
    st.markdown("---")
    
    # Individual setup action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Database download button - only enabled if database is missing
        if st.button("📥 Download Database", disabled=setup_status["database_exists"]):
            with st.spinner("Downloading database..."):
                if download_database():
                    st.success("Database downloaded successfully!")
                    st.rerun()
                else:
                    st.error("Error downloading database")
    
    with col2:
        # Vector store initialization - only enabled if not already initialized
        if st.button("🔄 Initialize Vector Store", disabled=setup_status["vector_store_exists"]):
            with st.spinner("Initializing vector store..."):
                if initialize_vector_store():
                    st.success("Vector store initialized successfully!")
                    st.rerun()
                else:
                    st.error("Error initializing vector store")
    
    with col3:
        # Complete setup button - performs all required setup steps
        if st.button("🚀 Complete Setup", type="primary"):
            with st.spinner("Running complete setup..."):
                if run_full_setup():
                    st.success("Setup completed successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Error during setup")
    
    st.markdown("---")
    st.info("💡 **Note:** Complete setup will automatically download the database and initialize the vector store.")
    
else:
    # === MAIN CHAT INTERFACE ===
    # Setup completed - display normal chat interface
    
    # Update database with current dates for realistic demo experience
    if setup_status["setup_complete"]:
        db = update_dates(local_file)
    
    # Chat message container for conversation display
    chat_container = st.container()
    
    # === MESSAGE PROCESSING ===
    # Handle user input and conversation flow
    if prompt := st.chat_input("Type your message..."):
        # Add user message to conversation history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Configuration for graph execution with user context
        config = {
            "configurable": {
                "passenger_id": passenger_id,
                "thread_id": st.session_state.thread_id,
            }
        }
        
        # === HUMAN APPROVAL WORKFLOW ===
        # Handle approval requests for sensitive operations
        if st.session_state.waiting_for_approval:
            if prompt.strip().lower() == "y":
                # User approved the operation - continue execution
                result = graph.invoke(None, config)
            else:
                # User denied the operation - provide explanation and continue
                result = graph.invoke(
                    {
                        "messages": [
                            ToolMessage(
                                tool_call_id=st.session_state.pending_event["messages"][-1].tool_calls[0]["id"],
                                content=f"API call denied by user. Reasoning: '{prompt}'. Continue assisting, accounting for the user's input.",
                            )
                        ]
                    },
                    config,
                )
            
            # Reset approval state after handling
            st.session_state.waiting_for_approval = False
            st.session_state.pending_event = None
            
            # Check if additional approvals are needed
            snapshot = graph.get_state(config)
            if snapshot.next:
                st.session_state.waiting_for_approval = True
                st.session_state.pending_event = {"messages": [result["messages"][-1]]}
        else:
            # === NORMAL CONVERSATION FLOW ===
            # Process new user message through the graph
            events = graph.stream(
                {"messages": ("user", prompt)}, 
                config, 
                stream_mode="values"
            )
            
            # Process all events and collect assistant responses
            for event in events:
                if event.get("messages"):
                    last_message = event["messages"][-1]
                    if hasattr(last_message, 'content') and last_message.content:
                        # Add assistant response to conversation history
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": last_message.content
                        })
            
            # === APPROVAL REQUEST DETECTION ===
            # Check if the conversation was interrupted for human approval
            snapshot = graph.get_state(config)
            if snapshot.next:
                st.session_state.waiting_for_approval = True
                st.session_state.pending_event = event
                
                # Display approval request interface
                if event.get("messages"):
                    last_message = event["messages"][-1]
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        tool_call = last_message.tool_calls[0]
                        approval_msg = f"🔄 **Approval Request:**\n\n"
                        approval_msg += f"**Tool:** {tool_call['name']}\n"
                        approval_msg += f"**Parameters:** {tool_call['args']}\n\n"
                        approval_msg += "**Please confirm:** Type 'y' to approve or explain why you're declining."
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": approval_msg
                        })

    # === CONVERSATION DISPLAY ===
    # Render all messages in the conversation history
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # === STATUS INDICATORS ===
    # Display current system status and workflow information
    if st.session_state.waiting_for_approval:
        st.warning("⏳ Waiting for your approval to proceed with the requested action.")
    
    # Display conversation thread ID for debugging and support
    with st.sidebar:
        st.markdown("---")
        st.caption(f"Thread ID: {st.session_state.thread_id}")
        st.caption(f"Messages: {len(st.session_state.messages)}")
        
        # Display active workflow if available (for debugging)
        if hasattr(st.session_state, 'current_workflow'):
            st.caption(f"Active workflow: {st.session_state.current_workflow}") 
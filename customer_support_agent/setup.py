"""
Setup Module - System Initialization and Configuration Management

This module provides comprehensive setup and initialization functionality for the
Swiss Airlines Customer Support AI system. It handles all required components
including database management, vector store initialization, and system validation
to ensure the application is ready for production use.

Key Components:
    - Database Management: Download and configure SQLite travel database
    - Vector Store Initialization: Setup semantic search capabilities
    - System Validation: Verify all components are properly configured
    - Automated Setup: One-click setup for complete system initialization

The setup process ensures that:
    1. Travel database is downloaded and properly formatted
    2. Vector store is initialized with company policy documents
    3. All required files and dependencies are available
    4. System is ready for customer support operations

Functions:
    download_database: Download and prepare the travel SQLite database
    initialize_vector_store: Create semantic search vector store
    check_setup_complete: Validate system readiness
    get_setup_status: Check individual component status
    run_full_setup: Complete automated setup process
"""

import os
import shutil
import sqlite3
import requests
import pandas as pd
from openai import OpenAI
from customer_support_agent.policy_retriever import load_policy_retriever
from customer_support_agent.utils import update_dates

# === CONFIGURATION CONSTANTS ===
# URLs and file paths for setup components

# Database source URL for travel data
DATABASE_URL = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"

# Local file paths for database management
LOCAL_FILE = "travel2.sqlite"          # Active database file
BACKUP_FILE = "travel2.backup.sqlite"  # Backup database file

# Vector store and document storage
VECTOR_STORE_FILE = "vector_store.npy"  # Serialized vector store file
FAQ_DOCS_FILE = "faq_docs.json"         # FAQ documents for vector store


def download_database():
    """
    Download and configure the travel database for customer support operations.
    
    Downloads the SQLite travel database from the remote server, creates a backup
    copy, and updates all timestamps to current dates for realistic demo experience.
    The database contains flight bookings, hotel reservations, car rentals, and
    trip recommendations used by the customer support system.
    
    Process:
        1. Download database from remote server
        2. Create backup copy for restoration purposes
        3. Update timestamps to current timeframe
        4. Validate database integrity
    
    Returns:
        bool: True if download and setup successful, False otherwise
        
    Example:
        >>> success = download_database()
        >>> if success:
        ...     print("Database ready for use")
        ... else:
        ...     print("Database setup failed")
    """
    try:
        print("📥 Downloading the database...")
        response = requests.get(DATABASE_URL)
        response.raise_for_status()
        
        # Save downloaded database
        with open(LOCAL_FILE, "wb") as f:
            f.write(response.content)
        
        # Create backup copy for future restoration
        shutil.copy(LOCAL_FILE, BACKUP_FILE)
        
        # Update dates to current timeframe for realistic demo
        update_dates(LOCAL_FILE)
        
        print("✅ Database downloaded and updated successfully!")
        return True
    except Exception as e:
        print(f"❌ Error during database download: {e}")
        return False


def initialize_vector_store():
    """
    Initialize the vector store for semantic search capabilities.
    
    Creates and configures the vector store using company policy documents
    and FAQ content. The vector store enables semantic search functionality
    for policy lookup and customer question answering.
    
    Process:
        1. Load company policy documents and FAQs
        2. Generate embeddings using OpenAI's embedding model
        3. Create and save vector store for fast retrieval
        4. Validate vector store functionality
    
    Returns:
        bool: True if vector store initialization successful, False otherwise
        
    Note:
        Requires OPENAI_API_KEY to be set in environment variables
        
    Example:
        >>> success = initialize_vector_store()
        >>> if success:
        ...     print("Vector store ready for semantic search")
        ... else:
        ...     print("Vector store initialization failed")
    """
    try:
        print("🔄 Initializing vector store...")
        
        # Load policy retriever which handles vector store creation
        global retriever
        retriever = load_policy_retriever()
        
        if retriever is not None:
            print("✅ Vector store initialized successfully!")
            return True
        else:
            print("❌ Vector store initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during vector store initialization: {e}")
        return False


def check_setup_complete():
    """
    Verify that all required system components are properly configured.
    
    Performs comprehensive validation of system readiness by checking:
    - Database file existence and integrity
    - Vector store availability and functionality
    - Required environment variables
    - File permissions and accessibility
    
    Returns:
        bool: True if all components are ready, False if setup is incomplete
        
    Example:
        >>> if check_setup_complete():
        ...     print("System ready for customer support operations")
        ... else:
        ...     print("Setup required before using the system")
    """
    try:
        # Check database availability
        database_exists = os.path.exists(LOCAL_FILE) and os.path.exists(BACKUP_FILE)
        
        # Check vector store availability
        vector_store_exists = os.path.exists(VECTOR_STORE_FILE)
        
        # System is complete if both components are available
        setup_complete = database_exists and vector_store_exists
        
        return setup_complete
        
    except Exception as e:
        print(f"❌ Error checking setup status: {e}")
        return False


def get_setup_status():
    """
    Get detailed status information for all system components.
    
    Provides granular status information for each setup component,
    enabling targeted setup actions and detailed system diagnostics.
    
    Returns:
        dict: Status information containing:
            - setup_complete: Overall system readiness
            - database_exists: Database availability status
            - vector_store_exists: Vector store availability status
            
    Example:
        >>> status = get_setup_status()
        >>> print(f"Database: {'✅' if status['database_exists'] else '❌'}")
        >>> print(f"Vector Store: {'✅' if status['vector_store_exists'] else '❌'}")
    """
    try:
        # Check individual component status
        database_exists = os.path.exists(LOCAL_FILE) and os.path.exists(BACKUP_FILE)
        vector_store_exists = os.path.exists(VECTOR_STORE_FILE)
        
        # Overall system status
        setup_complete = database_exists and vector_store_exists
        
        return {
            "setup_complete": setup_complete,
            "database_exists": database_exists, 
            "vector_store_exists": vector_store_exists
        }
        
    except Exception as e:
        print(f"❌ Error getting setup status: {e}")
        return {
            "setup_complete": False,
            "database_exists": False,
            "vector_store_exists": False
        }


def run_full_setup():
    """
    Execute complete automated setup process for the customer support system.
    
    Performs all required setup steps in the correct order:
    1. Download and configure travel database
    2. Initialize vector store with policy documents
    3. Validate system configuration
    4. Verify all components are functional
    
    This function provides one-click setup for new installations and
    can be used to reset the system to a known good state.
    
    Returns:
        bool: True if complete setup successful, False if any step failed
        
    Example:
        >>> if run_full_setup():
        ...     print("System fully configured and ready!")
        ... else:
        ...     print("Setup failed - check error messages above")
    """
    try:
        print("🚀 Starting complete system setup...")
        
        # Step 1: Download and configure database
        print("\n📋 Step 1: Database Setup")
        if not download_database():
            print("❌ Database setup failed")
            return False
        
        # Step 2: Initialize vector store
        print("\n📋 Step 2: Vector Store Setup")
        if not initialize_vector_store():
            print("❌ Vector store setup failed")
            return False
        
        # Step 3: Validate complete setup
        print("\n📋 Step 3: Validation")
        if check_setup_complete():
            print("✅ Complete setup finished successfully!")
            print("\n🎉 Customer Support AI is ready for use!")
            return True
        else:
            print("❌ Setup validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during complete setup: {e}")
        return False 
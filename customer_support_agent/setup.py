import os
import shutil
import sqlite3
import requests
import pandas as pd
from openai import OpenAI
from customer_support_agent.policy_retriever import load_policy_retriever
from customer_support_agent.utils import update_dates

# Configurazione percorsi
DATABASE_URL = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"
LOCAL_FILE = "travel2.sqlite"
BACKUP_FILE = "travel2.backup.sqlite"
VECTOR_STORE_FILE = "vector_store.npy"  # File per salvare il vector store
FAQ_DOCS_FILE = "faq_docs.json"  # File per salvare i documenti FAQ

def download_database():
    """
    Scarica il database SQLite dal server remoto
    """
    try:
        print("📥 Scaricando il database...")
        response = requests.get(DATABASE_URL)
        response.raise_for_status()
        
        with open(LOCAL_FILE, "wb") as f:
            f.write(response.content)
        
        # Crea il backup
        shutil.copy(LOCAL_FILE, BACKUP_FILE)
        
        # Aggiorna le date per renderle attuali
        update_dates(LOCAL_FILE)
        
        print("✅ Database scaricato e aggiornato con successo!")
        return True
    except Exception as e:
        print(f"❌ Errore durante il download del database: {e}")
        return False

def initialize_vector_store():
    """
    Inizializza il vector store con le FAQ
    """
    try:
        print("🔄 Inizializzando il vector store...")
        
        # Verifica che ci sia una chiave API OpenAI
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY non trovata nelle variabili d'ambiente")
            return False
        
        oai_client = OpenAI()
        
        # Carica il retriever (questo scarica le FAQ e crea gli embeddings)
        retriever = load_policy_retriever(oai_client)
        
        # Salva il vector store per riutilizzo futuro
        import numpy as np
        import json
        
        np.save(VECTOR_STORE_FILE, retriever._arr)
        
        with open(FAQ_DOCS_FILE, "w") as f:
            json.dump(retriever._docs, f)
        
        print("✅ Vector store inizializzato con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante l'inizializzazione del vector store: {e}")
        return False

def check_setup_complete():
    """
    Controlla se il setup è completo (database e vector store esistono)
    """
    db_exists = os.path.exists(LOCAL_FILE) and os.path.exists(BACKUP_FILE)
    vector_exists = os.path.exists(VECTOR_STORE_FILE) and os.path.exists(FAQ_DOCS_FILE)
    
    return db_exists and vector_exists

def get_setup_status():
    """
    Restituisce lo stato dettagliato del setup
    """
    status = {
        "database_exists": os.path.exists(LOCAL_FILE) and os.path.exists(BACKUP_FILE),
        "vector_store_exists": os.path.exists(VECTOR_STORE_FILE) and os.path.exists(FAQ_DOCS_FILE),
        "setup_complete": False
    }
    
    status["setup_complete"] = status["database_exists"] and status["vector_store_exists"]
    
    return status

def run_full_setup():
    """
    Esegue il setup completo: scarica database e inizializza vector store
    """
    print("🚀 Avvio setup completo...")
    
    # Step 1: Download database
    db_success = download_database()
    if not db_success:
        return False
    
    # Step 2: Initialize vector store
    vs_success = initialize_vector_store()
    if not vs_success:
        return False
    
    print("🎉 Setup completato con successo!")
    return True

def load_cached_vector_store():
    """
    Carica il vector store dai file salvati
    """
    try:
        import numpy as np
        import json
        from customer_support_agent.policy_retriever import VectorStoreRetriever
        from openai import OpenAI
        
        # Carica i dati salvati
        vectors = np.load(VECTOR_STORE_FILE)
        with open(FAQ_DOCS_FILE, "r") as f:
            docs = json.load(f)
        
        # Ricrea il retriever
        oai_client = OpenAI()
        retriever = VectorStoreRetriever(docs, vectors.tolist(), oai_client)
        
        return retriever
        
    except Exception as e:
        print(f"❌ Errore durante il caricamento del vector store: {e}")
        return None 
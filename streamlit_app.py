import streamlit as st
import uuid
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage

# Carica le variabili d'ambiente
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

# Configurazione della pagina
st.set_page_config(
    page_title="Customer Support AI",
    page_icon="✈️",
    layout="wide"
)

# Inizializza lo stato della sessione
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "waiting_for_approval" not in st.session_state:
    st.session_state.waiting_for_approval = False
if "pending_event" not in st.session_state:
    st.session_state.pending_event = None
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = check_setup_complete()

# Controlla lo stato del setup
setup_status = get_setup_status()

# Sidebar per configurazioni
st.sidebar.title("Configurazioni")
passenger_id = st.sidebar.text_input(
    "Passenger ID", 
    value="3442 587242",
    help="ID del passeggero per recuperare le informazioni del volo"
)

if st.sidebar.button("Nuova Conversazione"):
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.waiting_for_approval = False
    st.session_state.pending_event = None
    st.rerun()

# Titolo principale
st.title("🛫 Customer Support AI")
st.markdown("Assistente AI per prenotazioni di voli, hotel, noleggio auto ed escursioni")

# Controlla se il setup è completo
if not setup_status["setup_complete"]:
    # Mostra interfaccia di setup
    st.warning("⚠️ Setup iniziale richiesto")
    st.markdown("Prima di utilizzare l'assistente, è necessario scaricare il database e inizializzare il vector store.")
    
    # Mostra lo stato attuale
    col1, col2 = st.columns(2)
    
    with col1:
        if setup_status["database_exists"]:
            st.success("✅ Database già scaricato")
        else:
            st.error("❌ Database non trovato")
    
    with col2:
        if setup_status["vector_store_exists"]:
            st.success("✅ Vector store già inizializzato")
        else:
            st.error("❌ Vector store non trovato")
    
    st.markdown("---")
    
    # Pulsanti per azioni individuali
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Scarica Database", disabled=setup_status["database_exists"]):
            with st.spinner("Scaricando database..."):
                if download_database():
                    st.success("Database scaricato con successo!")
                    st.rerun()
                else:
                    st.error("Errore durante il download del database")
    
    with col2:
        if st.button("🔄 Inizializza Vector Store", disabled=setup_status["vector_store_exists"]):
            with st.spinner("Inizializzando vector store..."):
                if initialize_vector_store():
                    st.success("Vector store inizializzato con successo!")
                    st.rerun()
                else:
                    st.error("Errore durante l'inizializzazione del vector store")
    
    with col3:
        if st.button("🚀 Setup Completo", type="primary"):
            with st.spinner("Eseguendo setup completo..."):
                if run_full_setup():
                    st.success("Setup completato con successo!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Errore durante il setup")
    
    st.markdown("---")
    st.info("💡 **Nota:** Il setup completo scaricherà il database e inizializzerà il vector store automaticamente.")
    
else:
    # Setup completato - mostra la chat normale
    
    # Aggiorna il database con le date corrette (solo se setup è completo)
    if setup_status["setup_complete"]:
        db = update_dates(local_file)
    
    # Area della chat
    chat_container = st.container()
    
    # Input per i messaggi
    if prompt := st.chat_input("Scrivi il tuo messaggio..."):
        # Aggiungi il messaggio dell'utente
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Configurazione per il grafo
        config = {
            "configurable": {
                "passenger_id": passenger_id,
                "thread_id": st.session_state.thread_id,
            }
        }
        
        # Gestisci le approvazioni
        if st.session_state.waiting_for_approval:
            if prompt.strip().lower() == "y":
                # Approva l'azione
                result = graph.invoke(None, config)
            else:
                # Nega l'azione con spiegazione
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
            
            # Reset dello stato di attesa
            st.session_state.waiting_for_approval = False
            st.session_state.pending_event = None
            
            # Controlla se ci sono altre interruzioni
            snapshot = graph.get_state(config)
            if snapshot.next:
                st.session_state.waiting_for_approval = True
                st.session_state.pending_event = {"messages": [result["messages"][-1]]}
        else:
            # Nuova conversazione normale
            events = graph.stream(
                {"messages": ("user", prompt)}, 
                config, 
                stream_mode="values"
            )
            
            # Processa gli eventi
            for event in events:
                if event.get("messages"):
                    last_message = event["messages"][-1]
                    if hasattr(last_message, 'content') and last_message.content:
                        # Aggiungi la risposta dell'assistente
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": last_message.content
                        })
            
            # Controlla se ci sono interruzioni
            snapshot = graph.get_state(config)
            if snapshot.next:
                st.session_state.waiting_for_approval = True
                st.session_state.pending_event = event
                
                # Mostra il messaggio di richiesta approvazione
                if event.get("messages"):
                    last_message = event["messages"][-1]
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        tool_call = last_message.tool_calls[0]
                        approval_msg = f"🔄 **Richiesta di approvazione:**\n\n"
                        approval_msg += f"**Strumento:** {tool_call['name']}\n"
                        approval_msg += f"**Parametri:** {tool_call['args']}\n\n"
                        approval_msg += "Vuoi che proceda con questa azione?\n"
                        approval_msg += "- Scrivi **'y'** per approvare\n"
                        approval_msg += "- Oppure spiega cosa vorresti cambiare"
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": approval_msg
                        })

    # Visualizza i messaggi della chat
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

# Stato della conversazione nella sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("**Stato Sistema:**")

# Mostra stato setup
if setup_status["setup_complete"]:
    st.sidebar.success("✅ Setup completato")
else:
    st.sidebar.error("❌ Setup richiesto")

# Mostra dettagli setup
with st.sidebar.expander("Dettagli Setup"):
    st.write(f"Database: {'✅' if setup_status['database_exists'] else '❌'}")
    st.write(f"Vector Store: {'✅' if setup_status['vector_store_exists'] else '❌'}")

# Stato conversazione (solo se setup è completo)
if setup_status["setup_complete"]:
    st.sidebar.markdown("**Stato Conversazione:**")
    st.sidebar.markdown(f"Thread ID: `{st.session_state.thread_id[:8]}...`")
    st.sidebar.markdown(f"Messaggi: {len(st.session_state.messages)}")
    
    if st.session_state.waiting_for_approval:
        st.sidebar.warning("⏳ In attesa di approvazione")
    else:
        st.sidebar.success("✅ Pronto per nuovi messaggi") 
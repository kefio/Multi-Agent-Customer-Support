from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda, Runnable, RunnableConfig

from langgraph.prebuilt.tool_node import ToolNode

import shutil
import sqlite3

import pandas as pd
from typing import Callable

from customer_support_agent.state import State

local_file = "travel2.sqlite"
backup_file = "travel2.backup.sqlite"

######### Shared nodes utilities with sub-graphs #########
class Assistant:
    """
    This class is used to create a shared assistant node that can be used in the main graph and in the sub-graphs
    """
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}
    
def pop_dialog_state(state: State) -> dict:
    """
    pop dialog stack and return to primary assistant

    This lets the full graph explicitly track the dialog flow and delegate control to specific sub-graphs
    """
    messages = []
    # se l'ultimo messaggio è un tool call allora aggiungiamo 
    # un messaggio di tool per riprendere la conversazione con il primario
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="Resuming Dialog with Primary Assistant. Please reflect on the past conversation and assist the user with their request."),
                tool_call_id=state["messages"][-1].tool_calls[0]["id"]

                )
    return {
        "dialog_state": "pop",
        "messages": messages
        }

def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    """
    Factory function to create an entry point for a sub-graph
    """
    def entry_node(state: State) -> dict:
        """
        Entry point for a sub-graph
        """

        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "dialog_state": new_dialog_state,
            "messages": [
                ToolMessage(
                   content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id
                    )
                ]
            }
    return entry_node

def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: list) -> ToolNode:
    """
    Crea un ToolNode con fallback per gestire errori.
    Usa l'implementazione ufficiale di LangGraph.
    """

    # Ritorna un ToolNode con fallback per gestire errori. Dove RunnableLambda è una funzione che ritorna un Runnable.
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)


# Convert the flights to present time for our tutorial
def update_dates(file):
    shutil.copy(backup_file, file)
    conn = sqlite3.connect(file)
    cursor = conn.cursor()

    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table';", conn
    ).name.tolist()
    tdf = {}
    for t in tables:
        tdf[t] = pd.read_sql(f"SELECT * from {t}", conn)

    example_time = pd.to_datetime(
        tdf["flights"]["actual_departure"].replace("\\N", pd.NaT)
    ).max()
    current_time = pd.to_datetime("now").tz_localize(example_time.tz)
    time_diff = current_time - example_time

    tdf["bookings"]["book_date"] = (
        pd.to_datetime(tdf["bookings"]["book_date"].replace("\\N", pd.NaT), utc=True)
        + time_diff
    )

    datetime_columns = [
        "scheduled_departure",
        "scheduled_arrival",
        "actual_departure",
        "actual_arrival",
    ]
    for column in datetime_columns:
        tdf["flights"][column] = (
            pd.to_datetime(tdf["flights"][column].replace("\\N", pd.NaT)) + time_diff
        )

    for table_name, df in tdf.items():
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    del df
    del tdf
    conn.commit()
    conn.close()

    return file
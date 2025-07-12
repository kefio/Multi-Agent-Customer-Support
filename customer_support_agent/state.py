from typing import Annotated

from typing_extensions import TypedDict
from typing import Annotated, Literal, Optional
from langgraph.graph.message import AnyMessage, add_messages

def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    dialog_state: Annotated[
                    list[Literal[
                        "assistant", 
                        "update_flight",
                        "book_car_rental",
                        "book_hotel",
                        "book_excursion",
                        ]], 
            update_dialog_stack]

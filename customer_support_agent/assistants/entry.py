from customer_support_agent.state import State
from customer_support_agent.tools import fetch_user_flight_information


def user_info_node(state: State) -> State:
    return {"user_info": fetch_user_flight_information.invoke({})}


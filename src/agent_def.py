
from agents import Agent, handoff
from src.tools import faq_lookup_tool, update_seat, book_seat, find_available_flights,on_seat_booking_handoff
from src.model import model, AirlineAgentContext
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX



### AGENTS

faq_agent = Agent[AirlineAgentContext](
    name="FAQ Agent",
    handoff_description="A helpful agent that can answer questions about the airline.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are an FAQ agent. If you are speaking to a customer, you probably were transferred to from the triage agent.
    Use the following routine to support the customer.
    # Routine
    1. Identify the last question asked by the customer.
    2. Use the faq lookup tool to answer the question. Do not rely on your own knowledge.
    3. If you cannot answer the question, transfer back to the triage agent.""",
    tools=[faq_lookup_tool],
    model=model,
)

flight_booking_agent = Agent[AirlineAgentContext](
    name="Flight Booking Agent",
    handoff_description="A helpful agent that can book a flight or update a seat on a flight.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a flight booking agent. If you are speaking to a customer, you probably were transferred to from the triage agent or flight search agent.
    Use the following routing to support the customer in case of booking a new seat in flight
    # Routine
    1. Ask for flight number, if they dont provide one, transfer to flight search agent to search for flights.
    Use the following routine to support the customer in case of updating their seat
    # Routine
    1. Ask for their confirmation number.
    2. Ask the customer what their desired seat number is.
    3. Use the update seat tool to update the seat on the flight.
    If the customer asks a question that is not related to the routine, transfer back to the triage agent. """,
    tools=[update_seat, book_seat],
    model=model,
)

flight_search_agent = Agent[AirlineAgentContext](
    name="Flight Search Agent",
    handoff_description="A helpful agent that can find flights between two cities",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a flight searching agent. If you are speaking to a customer, you probably were transferred to from the triage agent.
    Use the following routing to support the customer in case of searching for flights
    # Routing
    1. Ask for departing city if not in the user question
    2. Ask for arriving city if not in the user question
    3. Use the list_all_flights tool to get the list of available flights.
    If the customer asks a question that is not related to the routine, transfer back to the triage agent.
    """,
    tools=[find_available_flights],
    model=model,
)

triage_agent = Agent[AirlineAgentContext](
    name="Triage Agent",
    handoff_description="A triage agent that can delegate a customer's request to the appropriate agent.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful triaging agent. You can use your tools to delegate questions to other appropriate agents."
    ),
    handoffs=[
        faq_agent,
        flight_search_agent,
        handoff(agent=flight_booking_agent, on_handoff=on_seat_booking_handoff),
    ],
    model=model
)

flight_search_agent.handoffs.append(triage_agent)
flight_search_agent.handoffs.append(flight_booking_agent)
faq_agent.handoffs.append(triage_agent)
flight_booking_agent.handoffs.append(triage_agent)
flight_booking_agent.handoffs.append(flight_search_agent)

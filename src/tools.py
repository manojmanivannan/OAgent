import random
import requests
from agents import function_tool, RunContextWrapper
from model import AirlineAgentContext
from itertools import product
from chroma import client as chroma_client


@function_tool(
    name_override="find_available_flights",
    description_override="List all flights between two cities.",
)
async def find_available_flights(
    context: RunContextWrapper[AirlineAgentContext], from_city: str, to_city: str
) -> str:
    """
    List options of flights for two given cities
    """
    # get the flights available by requesting the endpoint /flights?from_city=...&to_city=...
    try:
        flights = requests.get(
            "http://flight_server:8000/flights/search",
            params={"from_city": from_city, "to_city": to_city},
        ).json()

        context.context.from_city = from_city
        context.context.to_city = to_city
        return "\n".join(
            [
                f"Flight {s.get('flight_number')} - departing at {s.get('departing_time')}"
                for s in flights
            ]
        )  
    except Exception as e:
        print(e)
        return f"Error: {e}"


@function_tool(
    name_override="faq_lookup_tool",
    description_override="Lookup frequently asked questions.",
)
async def faq_lookup_tool(question: str) -> str:
    result = chroma_client.similarity_search(question)

    return "FAQ result\n" + result


@function_tool(
    name_override="book_flight_seat",
    description_override="Book a flight seat.",
)
async def book_flight_seat(
    context: RunContextWrapper[AirlineAgentContext],
    flight_number: str,
    passenger_name: str = None,
    no_of_seats: int = 1,
) -> str:
    """
    Book a new flight given from and to cities and return flight confirmation
    """
    # get the response content as list
    flights = requests.get(
        f"http://flight_server:8000/bookings/book",
        params={"flight_number": flight_number,
                "passenger_name": passenger_name,
                "no_of_seats": no_of_seats},
    ).json()

    assert passenger_name is not None, "Please provide the passenger name"
    assert context.context.from_city is not None, (
        "Please find flights using flight search agent"
    )
    assert context.context.to_city is not None, (
        "Please find flights using flight search agent"
    )
    assert flight_number in [s.get("flight_number") for s in flights], (
        f"Flight {flight_number} does not exist. Available flights are {find_available_flights(from_city=context.context.from_city, to_city=context.context.to_city)}"
    )
    context.context.passenger_name = passenger_name
    context.context.flight_number = flight_number

    response = requests.post(
        f"http://flight_server:8000/bookings/book",
        params={
            "flight_number": flight_number,
            "passenger_name": passenger_name,
            "no_of_seats": no_of_seats,
        },
    )

    if response.status_code != 200:
        return response.json().get("detail")

    booking_data = response.json()
    context.context.seat_numbers = booking_data.get("seat_numbers")
    context.context.confirmation_number = booking_data.get(
        "confirmation_number")

    return f"Booking number {context.context.confirmation_number} confirmed | flight {flight_number} from {context.context.from_city} to {context.context.to_city} with seat numbers {', '.join(context.context.seat_numbers)} booked for {passenger_name}"


@function_tool(
    name_override="update_flight_seat",
    description_override="Update the seat for a given confirmation number.",
)
async def update_flight_seat(
    context: RunContextWrapper[AirlineAgentContext],
    confirmation_number: str,
    new_seat: str,
) -> str:
    """
    Update the seat for a given confirmation number.

    Args:
        confirmation_number: The confirmation number for the flight.
        new_seat: The new seat to update to.
    """
    # Update the context based on the customer's input
    assert context.context.confirmation_number == confirmation_number, (
        f"Booking confirmation {confirmation_number} does not exist, Please try again."
    )

    availabe_seats = (
        requests.get(
            f"http://flight_server:8000/flights?flight_number={context.context.flight_number}"
        )
        .json()[0]
        .get("available_seats")
    )

    assert new_seat in availabe_seats, f"Only seats {availabe_seats} are available"
    context.context.seat_number = new_seat
    # Ensure that the flight number has been set by the incoming handoff
    assert context.context.flight_number is not None, "Flight number is required"
    response = requests.put(
        f"http://flight_server:8000/bookings/amend/{context.context.flight_number}",)
    return f"Updated seat to {new_seat} for confirmation number {confirmation_number}"


# HOOKS


async def on_seat_booking_handoff(
    context: RunContextWrapper[AirlineAgentContext],
) -> None:
    flight_number = f"FL-{random.randint(100, 999)}"
    # context.context.flight_number = flight_number

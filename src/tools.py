import random
import requests
import logging  # Added logging
from agents import function_tool, RunContextWrapper
from model import AirlineAgentContext
from itertools import product
from chroma import client as chroma_client

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
    logging.info(f"Searching for flights from {from_city} to {to_city}")
    try:
        flights = requests.get(
            "http://flight_server:8000/flights/search",
            params={"from_city": from_city, "to_city": to_city},
        ).json()
        logging.info(f"Found {len(flights)} flights from {from_city} to {to_city}")
        context.context.from_city = from_city
        context.context.to_city = to_city
        return "\n".join(
            [
                f"Flight {s.get('flight_number')} - departing at {s.get('departing_time')}"
                for s in flights
            ]
        )
    except Exception as e:
        logging.error(f"Error while searching for flights: {e}")
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
    logging.info(
        f"Attempting to book {no_of_seats} seat(s) on flight {flight_number} for {passenger_name}"
    )
    try:
        assert passenger_name is not None, "Please provide the passenger name"
        assert context.context.from_city is not None, (
            "Please find flights using flight search agent"
        )
        assert context.context.to_city is not None, (
            "Please find flights using flight search agent"
        )

        available_flights = requests.get(
            f"http://flight_server:8000/flights/search",
            params={
                "from_city": context.context.from_city,
                "to_city": context.context.to_city,
            },
        ).json()

        assert flight_number in [s.get("flight_number") for s in available_flights], (
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
        context.context.confirmation_number = booking_data.get("confirmation_number")

        logging.info(
            f"Booking successful: Confirmation number {context.context.confirmation_number}"
        )
        return f"Booking number {context.context.confirmation_number} confirmed | flight {flight_number} from {context.context.from_city} to {context.context.to_city} with seat numbers {', '.join(context.context.seat_numbers)} booked for {passenger_name}"
    except Exception as e:
        logging.error(f"Error while booking flight: {e}")
        return f"Error: {e}"


@function_tool(
    name_override="update_flight_seat",
    description_override="Update the seat for a given confirmation number.",
)
async def update_flight_seat(
    context: RunContextWrapper[AirlineAgentContext],
    confirmation_number: str,
    no_of_seats: int = 1,
    from_seat: str = None,
    to_seat: str = None,
) -> str:
    """
    Update the seat for a given confirmation number.

    Args:
        confirmation_number: The confirmation number for the flight.
        no_of_seats: The number of seats to update.
        from_seat: The current seat number. 
        to_seat: The new seat number.
    """
    logging.info(
        f"Updating seat {from_seat} to {to_seat} for confirmation number {confirmation_number}"
    )
    
    if confirmation_number is None:
        assert context.context.confirmation_number is not None, (
            "Please provide a confirmation number or book a flight first."
        )
    context.context.confirmation_number = confirmation_number
    
    try:
        assert context.context.confirmation_number == confirmation_number, (
            f"Booking confirmation {confirmation_number} does not exist, Please try again."
        )
        if context.context.flight_number is None:
            response = requests.get(
                "http://flight_server:8000/bookings/flight",
                params={"confirmation_number": confirmation_number},
            )
            response.raise_for_status()
            context.context.flight_number = response.json().get("flight_number")
            
        logging.info(
            f"Fetching available seats for flight {context.context.flight_number}"
        )
        availabe_seats = (
            requests.get(
                "http://flight_server:8000/flights/search",
                params={
                    "flight_number": context.context.flight_number,
                },
            )
            .json()
        )
        logging.info(f"Available seats: {availabe_seats}")
        availabe_seats = availabe_seats[0].get("available_seats")
        
        assert to_seat in availabe_seats, f"Only seats {availabe_seats} are available"
        # context.context.seat_numbers = to_seat
        # Ensure that the flight number has been set by the incoming handoff
        # assert context.context.flight_number is not None, "Flight number is required"
        response = requests.put(
            "http://flight_server:8000/bookings/amend",
            params={
                "confirmation_number": confirmation_number,
                "seat_number_from": from_seat,
                "seat_number_to": to_seat,
            },
        )
        response.raise_for_status()
        logging.info(f"Seat updated successfully from {from_seat} to {to_seat}")
        return response.json()
    
    except Exception as e:
        logging.error(f"Error while updating seat: {e}")
        return f"Error: {e}"


# HOOKS


async def on_seat_booking_handoff(
    context: RunContextWrapper[AirlineAgentContext],
) -> None:
    flight_number = f"FL-{random.randint(100, 999)}"
    # context.context.flight_number = flight_number

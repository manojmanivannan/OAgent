import random
from agents import function_tool, RunContextWrapper
from src.model import AirlineAgentContext
from itertools import chain, product


def generate_flights():
    from_cities = [
        "New York",
        "London",
        "Tokyo",
        "Sydney",
        "Dubai",
        "Los Angeles",
        "Hong Kong",
        "Chicago",
        "Madrid",
        "Seoul",
    ]
    to_cities = [
        "Paris",
        "Berlin",
        "Mumbai",
        "Toronto",
        "Singapore",
        "Rome",
        "Beijing",
        "Bangkok",
        "Mexico City",
        "Cape Town",
    ]
    departing_times = [
        "00:15",
        "04:45",
        "08:20",
        "10:30",
        "12:10",
        "15:30",
        "18:50",
        "21:15",
        "23:55",
    ]

    flights = []
    flight_id = 1

    # Generate all combinations of from_cities and to_cities
    for from_city, to_city in product(from_cities, to_cities):
        if from_city != to_city:  # Exclude flights from a city to itself
            # Pick 3 unique departure times for each city pair
            times = random.sample(departing_times, 3)

            # Generate seats in a predictable order
            seat_columns = "A B C D E F".split()
            seat_rows = range(10, 15)
            available_seats = [
                f"{column}{row:02}" for column in seat_columns for row in seat_rows
            ]

            # Create 3 flights for each from-to combination
            for time in times:
                flights.append(
                    [f"FL{flight_id:03}", from_city, to_city, time, available_seats]
                )
                flight_id += 1

    return flights


@function_tool(
    name_override="list_all_flights",
    description_override="List all flights between two cities.",
)
async def find_available_flights(
    context: RunContextWrapper[AirlineAgentContext], from_city: str, to_city: str
) -> str:
    """
    List options of flights for two given cities
    """
    flights = generate_flights()
    available_flights = [
        (flight, from_c, to_c, time, seat)
        for flight, from_c, to_c, time, seat in flights
        if from_c == from_city and to_c == to_city
    ]

    context.context.from_city = from_city
    context.context.to_city = to_city
    return "\n".join(
        [f"Flight {fl} - departing at {t}" for fl, _, _, t, seats in available_flights]
    )  # Return up to 5 flights


@function_tool(
    name_override="faq_lookup_tool",
    description_override="Lookup frequently asked questions.",
)
async def faq_lookup_tool(question: str) -> str:
    if "bag" in question or "baggage" in question:
        return (
            "You are allowed to bring one bag on the plane. "
            "It must be under 50 pounds and 22 inches x 14 inches x 9 inches."
        )
    elif "seats" in question or "plane" in question:
        return (
            "There are 120 seats on the plane. "
            "There are 22 business class seats and 98 economy seats. "
            "Exit rows are rows 4 and 16. "
            "Rows 5-8 are Economy Plus, with extra legroom. "
        )
    elif "wifi" in question:
        return "We have free wifi on the plane, join Airline-Wifi"
    return "I'm sorry, I don't know the answer to that question."


@function_tool
async def book_seat(
    context: RunContextWrapper[AirlineAgentContext],
    flight_number: str,
    passenger_name: str = None,
) -> str:
    """
    Book a new flight given from and to cities and return flight confirmation
    """
    assert passenger_name is not None, "Please provide the passenger name"
    assert context.context.from_city is not None, (
        "Please find flights using flight search agent"
    )
    assert context.context.to_city is not None, (
        "Please find flights using flight search agent"
    )
    assert flight_number in [fno for fno, _, _, _, _ in generate_flights()], (
        f"Flight {flight_number} does not exist. Available flights are {find_available_flights(from_city=context.context.from_city, to_city=context.context.to_city)}"
    )
    context.context.passenger_name = passenger_name
    context.context.flight_number = flight_number
    context.context.seat_number = (
        f"{random.choice('A B C D E F'.split())}{random.randint(1, 10):02}"
    )

    context.context.confirmation_number = str(random.randint(1000, 9999))

    return f"Booking number {context.context.confirmation_number} confirmed | flight {flight_number} from {context.context.from_city} to {context.context.from_city} with seat number {context.context.seat_number} booked for {passenger_name}"


@function_tool
async def update_seat(
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
    availabe_seats = [
        seats
        for s, _, _, _, seats in generate_flights()
        if s == context.context.flight_number
    ][0]
    assert new_seat in availabe_seats, f"Only seats {availabe_seats} are available"
    context.context.seat_number = new_seat
    # Ensure that the flight number has been set by the incoming handoff
    assert context.context.flight_number is not None, "Flight number is required"
    return f"Updated seat to {new_seat} for confirmation number {confirmation_number}"


### HOOKS


async def on_seat_booking_handoff(
    context: RunContextWrapper[AirlineAgentContext],
) -> None:
    flight_number = f"FL-{random.randint(100, 999)}"
    # context.context.flight_number = flight_number

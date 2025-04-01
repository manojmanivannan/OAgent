
from database import Flight
from typing import List

####################### HELPER FUNCTIONS ########################################################


def format_flights_data(flights: List[Flight]):
    return [
        {
            "flight_number": f.flight_number,
            "departure_city": f.from_city,
            "arrival_city": f.to_city,
            "departing_time": f.departing_time,
            "arrival_time": f.arrival_time,
            "flight_duration": f.flight_duration,
            "available_seats": f.available_seats,
        }
        for f in flights
    ]

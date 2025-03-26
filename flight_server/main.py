from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal, Flight, Booking
import random
from typing import List


app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
            "available_seats": f.available_seats.split(","),
        }
        for f in flights
    ]


#### FLIGHT API #################################################################################

flights_router = APIRouter(prefix="/flights", tags=["flights"])


@flights_router.get("/list")
async def list_all_flights(db: Session = Depends(get_db)):
    flights = db.query(Flight).all()  # removed await
    return format_flights_data(flights)


@flights_router.get("/search")
async def search_flights(
    from_city: str = None,
    to_city: str = None,
    flight_number: str = None,
    db: Session = Depends(get_db),
):
    if flight_number:
        flights = (
            db.query(Flight).filter(Flight.flight_number == flight_number).all()
        )  # removed await
    elif from_city and to_city:
        flights = (
            db.query(Flight)
            .filter(Flight.from_city == from_city, Flight.to_city == to_city)
            .order_by(Flight.departing_time.asc())
            .all()
        )  # removed await
    elif from_city:
        flights = db.query(Flight).filter(Flight.from_city == from_city).all()
    elif to_city:
        flights = db.query(Flight).filter(Flight.to_city == to_city).all()
    else:
        flights = db.query(Flight).all()  # removed await

    return format_flights_data(flights)


#### BOOKING API #################################################################################

booking_router = APIRouter(prefix="/bookings", tags=["bookings"])


# list all bookings
@booking_router.get("/list")
async def list_booking_by_confirmation_or_passenger(
    confirmation_number: str = None,
    passenger_name: str = None,
    db: Session = Depends(get_db),
):
    if confirmation_number:
        bookings = [
            db.query(Booking)
            .filter(Booking.confirmation_number == confirmation_number)
            .first()
        ]  # Replace with await if needed
    elif passenger_name:
        bookings = [
            db.query(Booking).filter(Booking.passenger_name == passenger_name).first()
        ]  # Replace with await if needed
    else:
        bookings = db.query(Booking).all()  # Replace with await if needed
    return [
        {
            "flight_number": b.flight_number,
            "passenger_name": b.passenger_name,
            "seat_number": b.seat_number,
            "confirmation_number": b.confirmation_number,
        }
        for b in bookings
    ]


# make new booking
@booking_router.post("/book")
async def book_flight(
    flight_number: str,
    passenger_name: str,
    seat_number: str,
    db: Session = Depends(get_db),
):
    existing_confirmations = {
        booking.confirmation_number
        for booking in db.query(Booking.confirmation_number).all()
    }  # Consider: await db.query(...)

    while True:
        confirmation_number = "CONF" + str(random.randint(1000, 9999))
        if confirmation_number not in existing_confirmations:
            break

    booking = Booking(
        flight_number=flight_number,
        passenger_name=passenger_name,
        seat_number=seat_number,
        confirmation_number=confirmation_number,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


# amend booking
@booking_router.put("/amend")
async def amend_booking_by_confirmation_number(
    confirmation_number: str, new_seat_number: str, db: Session = Depends(get_db)
):
    booking = (
        db.query(Booking)
        .filter(Booking.confirmation_number == confirmation_number)
        .first()
    )  # Replace with await if needed
    booking.seat_number = new_seat_number
    db.commit()
    db.refresh(booking)
    return booking


# search all bookings for a flight
@booking_router.get("/search")
async def search_booking_by_flight(flight_number: str, db: Session = Depends(get_db)):
    bookings = db.query(Booking).filter(Booking.flight_number == flight_number).all()
    flight = db.query(Flight).filter(Flight.flight_number == flight_number).first()

    return [
        {
            "flight_number": flight.flight_number,
            "departure_city": flight.from_city,
            "arrival_city": flight.to_city,
            "departing_time": flight.departing_time,
            "arrival_time": flight.arrival_time,
            "flight_duration": flight.flight_duration,
            "bookings": [
                {
                    "passenger_name": b.passenger_name,
                    "seat_number": b.seat_number,
                    "confirmation_number": b.confirmation_number,
                }
                for b in bookings
            ],
        }
    ]


###############################################################################################
app.include_router(flights_router)
app.include_router(booking_router)

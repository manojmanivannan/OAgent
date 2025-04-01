from fastapi import Depends, APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal, Flight, Booking
import random
from typing import Annotated, Optional
import json
import logging  # Added logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#### BOOKING API #################################################################################

booking_router = APIRouter(prefix="/bookings", tags=["bookings"])


# list all bookings
@booking_router.get("/list")
async def list_booking_by_confirmation_or_passenger(
    confirmation_number: str = None,
    passenger_name: str = None,
    db: Session = Depends(get_db),
):
    logging.info(
        f"Listing bookings with confirmation_number={confirmation_number} or passenger_name={passenger_name}"
    )
    try:
        if confirmation_number:
            bookings = [
                db.query(Booking)
                .filter(Booking.confirmation_number == confirmation_number)
                .first()
            ]  # Replace with await if needed
        elif passenger_name:
            bookings = [
                db.query(Booking)
                .filter(Booking.passenger_name == passenger_name)
                .first()
            ]  # Replace with await if needed
        else:
            bookings = db.query(Booking).all()  # Replace with await if needed
        logging.info(f"Returned {len(bookings)} bookings")
        return [
            {
                "flight_number": b.flight_number,
                "passenger_name": b.passenger_name,
                "seat_number": b.seat_number,
                "confirmation_number": b.confirmation_number,
            }
            for b in bookings
        ]
    except Exception as e:
        logging.error(f"Error while listing bookings: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# make new booking
@booking_router.post("/book")
async def book_flight(
    flight_number: Annotated[
        str, Query(example="FL1234", regex="FL[0-9]{4}", max_length=6)
    ],
    passenger_name: Annotated[
        str,
        Query(
            example="Jon Doe",
            regex="^([a-zA-Z]{2,}\s[a-zA-Z]{1,}'?-?[a-zA-Z]{2,}\s?([a-zA-Z]{1,})?)",
            max_length=50,
        ),
    ],
    no_of_seats: Annotated[int, Query(example=1, ge=1, le=10)],
    db: Session = Depends(get_db),
):
    logging.info(
        f"Booking {no_of_seats} seat(s) on flight {flight_number} for {passenger_name}"
    )
    try:
        if flight_number not in [f.flight_number for f in db.query(Flight).all()]:
            raise HTTPException(
                status_code=404, detail=f"Flight {flight_number} not found"
            )

        available_seats = (
            db.query(Flight)
            .filter(Flight.flight_number == flight_number)
            .first()
            .available_seats
        )

        if not available_seats:
            raise HTTPException(
                status_code=400,
                detail=f"No seats are available for flight {flight_number}",
            )

        if no_of_seats > len(available_seats):
            raise HTTPException(
                status_code=400,
                detail=f"Only {len(available_seats)} seats are available for flight {flight_number}",
            )

        # Randomly select no_of_seats from available_seats
        if no_of_seats == 1:
            seat_numbers = [random.choice(available_seats)]
        else:
            # select continuous seats
            seat_numbers = available_seats[:no_of_seats]

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
            seat_numbers=seat_numbers,
            confirmation_number=confirmation_number,
        )

        # Update flight record to remove the booked seat from available_seats
        flight_obj = (
            db.query(Flight).filter(Flight.flight_number == flight_number).first()
        )
        flight_obj.available_seats = sorted(
            list(set(available_seats).difference(set(seat_numbers)))
        )

        db.add(booking)
        db.commit()
        db.refresh(booking)
        db.refresh(flight_obj)
        logging.info(f"Booking successful: Confirmation number {confirmation_number}")
        return booking
    except Exception as e:
        logging.error(f"Error while booking flight: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# amend booking
@booking_router.put("/amend")
async def amend_booking_by_confirmation_number(
    confirmation_number: Annotated[
        str, Query(example="CONF1234", regex="CONF[0-9]{4}", max_length=8)
    ],
    no_of_seats: Optional[Annotated[int, Query(example=1, ge=1, le=10)]] = None,
    seat_number_from: Optional[
        Annotated[
            str, Query(description="Change seat from", example="12A", max_length=4)
        ]
    ] = None,
    seat_number_to: Optional[
        Annotated[str, Query(description="Change seat to", example="12B", max_length=4)]
    ] = None,
    db: Session = Depends(get_db),
):
    logging.info(f"Amending booking {confirmation_number}")
    try:
        # Validate that only one of (no_of_seats) or (seat_number_from and seat_number_to) is provided
        if no_of_seats is not None and (seat_number_from or seat_number_to):
            raise HTTPException(
                status_code=400,
                detail="Provide either no_of_seats or both seat_number_from and seat_number_to, but not both",
            )
        if (seat_number_from and not seat_number_to) or (
            seat_number_to and not seat_number_from
        ):
            raise HTTPException(
                status_code=400,
                detail="Both seat_number_from and seat_number_to must be provided together",
            )

        # check if booking exists
        booking = (
            db.query(Booking)
            .filter(Booking.confirmation_number == confirmation_number)
            .first()
        )
        if not booking:
            raise HTTPException(
                status_code=404, detail=f"Booking {confirmation_number} not found"
            )

        flight = (
            db.query(Flight)
            .filter(Flight.flight_number == booking.flight_number)
            .first()
        )
        if not flight:
            raise HTTPException(
                status_code=404, detail=f"Flight {booking.flight_number} not found"
            )

        available_seats = list(flight.available_seats)
        booked_seats = list(booking.seat_numbers)
        # print(f"available_seats: {available_seats}")
        # print(f"booked_seats: {booked_seats}")
        # print("--------------------")
        # Handle seat_number_from and seat_number_to update
        if seat_number_from and seat_number_to:
            if seat_number_from not in booked_seats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Seat {seat_number_from} is not in the booked seats",
                )
            if seat_number_to not in available_seats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Seat {seat_number_to} is not available. Available seats are {available_seats}",
                )

            # move seat_number_from from booked_seats to available_seats
            booked_seats.remove(seat_number_from)
            # print(f"booked_seats: {booked_seats} after removing {seat_number_from}")
            available_seats.append(seat_number_from)
            # print(f"available_seats: {available_seats} after adding {seat_number_from}")
            # print("--------------------")

            # move seat_number_to from available_seats to booked_seats
            available_seats.remove(seat_number_to)
            # print(f"available_seats: {available_seats} after removing {seat_number_to}")
            booked_seats.append(seat_number_to)
            # print(f"booked_seats: {booked_seats} after adding {seat_number_to}")
            # print("--------------------")

            flight.available_seats = sorted(list(set(available_seats)))
            booking.seat_numbers = sorted(list(set(booked_seats)))

            db.commit()
            db.refresh(flight)
            db.refresh(booking)

            logging.info(f"Booking {confirmation_number} amended successfully")
            return booking

        # Handle no_of_seats update
        if no_of_seats is not None:
            if no_of_seats < len(booked_seats):
                # Reduce seats
                seats_to_release = booked_seats[no_of_seats:]
                booking.seat_numbers = booked_seats[:no_of_seats]
                flight.available_seats = sorted(available_seats + seats_to_release)
            elif no_of_seats > len(booked_seats):
                # Add seats
                additional_seats_needed = no_of_seats - len(booked_seats)
                if additional_seats_needed > len(available_seats):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Only {len(available_seats)} additional seats are available",
                    )
                new_seats = available_seats[:additional_seats_needed]
                booking.seat_numbers = sorted(list(set(booked_seats + new_seats)))
                flight.available_seats = sorted(
                    list(set(available_seats).difference(set(new_seats)))
                )

            db.commit()
            db.refresh(booking)
            db.refresh(flight)
            logging.info(f"Booking {confirmation_number} amended successfully")
            return booking

        raise HTTPException(
            status_code=400,
            detail="Either no_of_seats or both seat_number_from and seat_number_to must be provided",
        )
    except Exception as e:
        logging.error(f"Error while amending booking: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# search all bookings for a flight
@booking_router.get("/search")
async def search_booking_by_flight(flight_number: str, db: Session = Depends(get_db)):
    logging.info(f"Searching bookings for flight {flight_number}")
    try:
        bookings = (
            db.query(Booking).filter(Booking.flight_number == flight_number).all()
        )
        flight = db.query(Flight).filter(Flight.flight_number == flight_number).first()

        logging.info(f"Found {len(bookings)} bookings for flight {flight_number}")
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
    except Exception as e:
        logging.error(f"Error while searching bookings: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

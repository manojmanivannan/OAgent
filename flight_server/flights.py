
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal, Flight
from utils import format_flights_data

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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

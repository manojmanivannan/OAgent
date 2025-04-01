import logging
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal, Flight
from utils import format_flights_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info("Fetching all flights")
    flights = db.query(Flight).all()  # removed await
    logger.info(f"Retrieved {len(flights)} flights from the database")
    return format_flights_data(flights)


@flights_router.get("/search")
async def search_flights(
    from_city: str = None,
    to_city: str = None,
    flight_number: str = None,
    db: Session = Depends(get_db),
):
    logger.info(f"Searching flights with parameters: from_city={from_city}, to_city={to_city}, flight_number={flight_number}")
    if flight_number:
        flights = (
            db.query(Flight).filter(Flight.flight_number == flight_number).all()
        )  # removed await
        logger.info(f"Found {len(flights)} flights matching flight_number={flight_number}")
    elif from_city and to_city:
        flights = (
            db.query(Flight)
            .filter(Flight.from_city == from_city, Flight.to_city == to_city)
            .order_by(Flight.departing_time.asc())
            .all()
        )  # removed await
        logger.info(f"Found {len(flights)} flights from {from_city} to {to_city}")
    elif from_city:
        flights = db.query(Flight).filter(Flight.from_city == from_city).all()
        logger.info(f"Found {len(flights)} flights from {from_city}")
    elif to_city:
        flights = db.query(Flight).filter(Flight.to_city == to_city).all()
        logger.info(f"Found {len(flights)} flights to {to_city}")
    else:
        flights = db.query(Flight).all()  # removed await
        logger.info(f"Found {len(flights)} flights with no specific filters")

    return format_flights_data(flights)

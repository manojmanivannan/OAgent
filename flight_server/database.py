from sqlalchemy import create_engine, Column, Integer, String, Double
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random
from datetime import datetime, timedelta
import argparse, os


SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), './flights.db'))}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Flight(Base):
    __tablename__ = "flights"
    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String, unique=True, index=True)
    from_city = Column(String, index=True)
    to_city = Column(String, index=True)
    departing_time = Column(String)
    flight_duration = Column(Double)
    arrival_time = Column(String)
    available_seats = Column(String)  # comma-separated list of seats

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String, index=True)
    passenger_name = Column(String)
    seat_number = Column(String)
    confirmation_number = Column(String)
    
# Create all tables based on the defined models
Base.metadata.create_all(engine)

def seed_database(num_flights=10):
    """
    Populates the flight database with random flight information.
    """
    session = SessionLocal()
    cities = [
        "New York", "London", "Tokyo", "Sydney", "Dubai", "Los Angeles", "Hong Kong", "Chicago", "Madrid", "Seoul", "Paris", "Berlin", "Mumbai", "Toronto", "Singapore", "Rome", "Beijing", "Bangkok", "Mexico City", "Cape Town", "Cairo", "Moscow", "Istanbul", "Vienna", "Athens", "Lisbon", "Amsterdam", "Brussels", "Oslo", "Stockholm", "Helsinki", "Warsaw", ]
    existing_flight_numbers = {flight.flight_number for flight in session.query(Flight.flight_number).all()}  # Fetch all existing flight numbers
    
    if len(existing_flight_numbers) >= num_flights:
        print("Database already has enough flights.")
        return
    
    added = 0
    flights_to_add = []
    
    while added < num_flights:
        flight_number = "FL" + str(random.randint(1000, 9999))
        if flight_number in existing_flight_numbers:
            continue

        from_city = random.choice(cities)
        to_city = random.choice([c for c in cities if c != from_city])
        start_time = (datetime.now() + timedelta(hours=random.randint(1, 72)))
        departing_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        flight_duration = random.randint(1, 24) + random.random()
        arrival_time = (start_time + timedelta(hours=flight_duration)).strftime("%Y-%m-%d %H:%M:%S")
        # Generate a comma-separated list of 12 available seats (rows 1-3, seats A-D)
        available_seats = ",".join([f"{row}{seat}" for row in range(10,20) for seat in "ABCD"])
        flight = Flight(
            flight_number=flight_number,
            from_city=from_city,
            to_city=to_city,
            departing_time=departing_time,
            available_seats=available_seats,
            flight_duration=flight_duration,
            arrival_time=arrival_time
        )
        flights_to_add.append(flight)
        existing_flight_numbers.add(flight_number)  # Ensure no duplicates in future iterations
        added += 1

    session.bulk_save_objects(flights_to_add)  # Efficient bulk insert
    session.commit()
    session.close()



seed_database(100)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed flight database with random flights.")
    parser.add_argument("--num_flights", type=int, default=10, help="Number of flights to add.")
    args = parser.parse_args()
    seed_database(args.num_flights)
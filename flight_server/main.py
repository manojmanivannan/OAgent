from fastapi import FastAPI, Depends, APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
import random
from typing import List, Annotated
from booking import booking_router
from flights import flights_router


app = FastAPI()

###############################################################################################
app.include_router(flights_router)
app.include_router(booking_router)

# This module implements a booking service that allows users to create,
# retrieve, and delete bookings for movies on specific dates.

from http import HTTPStatus
from json import load, dump
from os import environ
from typing import TypeVar

import requests
from flask import Flask, jsonify
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from werkzeug.exceptions import (
    BadGateway,
    Conflict,
    HTTPException,
    NotFound,
    UnprocessableEntity,
)

app = Flask(__name__)

PORT = 3201
HOST = '0.0.0.0'
DB_PATH = "./databases/bookings.json"
# URLS for the schedule and movie services, can be overridden by environment variables
SCHEDULE_URL = environ.get("SCHEDULE_URL", "http://localhost:3202")
MOVIE_URL = environ.get("MOVIE_URL", "http://localhost:3200")
TIMEOUT = 5

with open(DB_PATH, 'r') as jsf:
    bookings = load(jsf)["bookings"]


def write(bookings):
    with open(DB_PATH, 'w') as f:
        dump({"bookings": bookings}, f)


T = TypeVar("T", bound=BaseModel)

# Input model for creating a new booking
class BookingInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    date: str = Field(pattern=r"^\d{8}$")
    movies: list[str] = Field(min_length=1)

# Response model for returning booking details
class DateBooking(BaseModel):
    date: str
    movies: list[str]

# Response model for returning user bookings
class BookingResponse(BaseModel):
    userid: str
    dates: list[DateBooking]


class BookingNotFoundError(NotFound):
    pass


class BookingDateNotFoundError(NotFound):
    pass


class BookingAlreadyExistsError(Conflict):
    pass


class UpstreamServiceError(BadGateway):
    pass


# Error handlers for custom exceptions

@app.errorhandler(BookingNotFoundError)
def handle_booking_not_found(e: BookingNotFoundError):
    return jsonify(error="Booking does not exist"), 404


@app.errorhandler(BookingDateNotFoundError)
def handle_booking_date_not_found(e: BookingDateNotFoundError):
    return jsonify(error="No booking for this date"), 404


@app.errorhandler(BookingAlreadyExistsError)
def handle_booking_exists(e: BookingAlreadyExistsError):
    return jsonify(error="Booking already exists for this date"), 409


@app.errorhandler(UpstreamServiceError)
def handle_upstream_error(e: UpstreamServiceError):
    return jsonify(error="An upstream service is unavailable"), 502


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    return jsonify(error=e.description), e.code


# Helper functions for finding and managing bookings
def find_user(userid: str) -> dict:
    for entry in bookings:
        if str(entry["userid"]) == str(userid):
            return entry
    raise BookingNotFoundError()

# Helper function to get or create a user booking entry
def get_or_create_user(userid: str) -> dict:
    for entry in bookings:
        if str(entry["userid"]) == str(userid):
            return entry
    entry = {"userid": userid, "dates": []}
    bookings.append(entry)
    return entry

# Helper function to find a specific date booking for a user
def find_date(entry: dict, date: str) -> dict:
    for d in entry["dates"]:
        if str(d["date"]) == str(date):
            return d
    raise BookingDateNotFoundError()

# Helper function to validate incoming JSON payloads against Pydantic models
def check_schedule(date: str, movies: list) -> None:
    try:
        r = requests.get(f"{SCHEDULE_URL}/schedule/{date}", timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise UpstreamServiceError() from exc

    if r.status_code == 404:
        raise UnprocessableEntity(description="Date is not scheduled")
    if r.status_code != 200:
        raise UpstreamServiceError()

    scheduled = r.json().get("movies", [])
    for movie in movies:
        if movie not in scheduled:
            raise UnprocessableEntity(
                description=f"Movie {movie} is not scheduled on {date}"
            )


@app.route("/", methods=['GET'])
def home():
    return "<h1 style='color:blue'>Welcome to the Booking service!</h1>"


# Route handlers for booking operations
@app.route("/bookings/<userid>", methods=["GET"])
def get_user_bookings(userid: str):
    return jsonify(find_user(userid)), HTTPStatus.OK


# Route handler for adding a new booking for a user
@app.route("/bookings/<userid>", methods=["POST"])
def add_booking(userid: str):
    check_schedule(payload.date, payload.movies)

    entry = get_or_create_user(userid)
    if any(str(d["date"]) == payload.date for d in entry["dates"]):
        raise BookingAlreadyExistsError()

    entry["dates"].append(payload.model_dump())
    write(bookings)
    return jsonify(entry), HTTPStatus.CREATED


# Route handler for getting detailed booking information for a specific date
@app.route("/bookings/<userid>/<date>", methods=["GET"])
def get_booking_details(userid: str, date: str):
    entry = find_user(userid)
    booking = find_date(entry, date)

    movies = []
    for movieid in booking["movies"]:
        try:
            r = requests.get(f"{MOVIE_URL}/movies/{movieid}", timeout=TIMEOUT)
        except requests.RequestException as exc:
            raise UpstreamServiceError() from exc
        movies.append(r.json() if r.status_code == 200 else {"id": movieid})

    return jsonify({"userid": userid, "date": date, "movies": movies}), HTTPStatus.OK


# Route handler for deleting a booking for a specific date
@app.route("/bookings/<userid>/<date>", methods=["DELETE"])
def delete_booking(userid: str, date: str):
    entry = find_user(userid)
    find_date(entry, date)
    entry["dates"] = [d for d in entry["dates"] if str(d["date"]) != str(date)]
    write(bookings)
    return "", HTTPStatus.NO_CONTENT


if __name__ == "__main__":
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)

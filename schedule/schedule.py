from http import HTTPStatus
from json import load, dump, loads
from typing import Any, Type, TypeVar

from flask import Flask, jsonify, request
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
)
from werkzeug.exceptions import (
    Conflict,
    HTTPException,
    NotFound,
    UnprocessableEntity,
)

app = Flask(__name__)

PORT = 3202
HOST = '0.0.0.0'
DB_PATH = "./databases/times.json"

with open(DB_PATH, 'r') as jsf:
    schedule = load(jsf)["schedule"]


def write(schedule):
    with open(DB_PATH, 'w') as f:
        dump({"schedule": schedule}, f)


T = TypeVar("T", bound=BaseModel)


class ScheduleInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    date: str = Field(pattern=r"^\d{8}$")
    movies: list[str] = Field(default_factory=list)


class ScheduleResponse(BaseModel):
    date: str
    movies: list[str]


def validate_payload(model: Type[T], payload: Any) -> T:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise UnprocessableEntity(description=loads(exc.json())) from exc


class ScheduleNotFoundError(NotFound):
    pass


class ScheduleAlreadyExistsError(Conflict):
    pass


@app.errorhandler(ScheduleNotFoundError)
def handle_schedule_not_found(e: ScheduleNotFoundError):
    return jsonify(error="Date does not exist"), 404


@app.errorhandler(ScheduleAlreadyExistsError)
def handle_schedule_exists(e: ScheduleAlreadyExistsError):
    return jsonify(error="Date already exists"), 409


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    return jsonify(error=e.description), e.code


def find_schedule(date: str) -> dict:
    for entry in schedule:
        if str(entry["date"]) == str(date):
            return entry
    raise ScheduleNotFoundError()


def find_schedule_index(date: str) -> int:
    for i, entry in enumerate(schedule):
        if str(entry["date"]) == str(date):
            return i
    raise ScheduleNotFoundError()


@app.route("/", methods=['GET'])
def home():
    return "<h1 style='color:blue'>Welcome to the Showtime service!</h1>"


@app.route("/schedule", methods=["GET"])
def get_schedule():
    return jsonify(schedule), HTTPStatus.OK


@app.route("/schedule/<date>", methods=["GET"])
def get_schedule_bydate(date: str):
    return jsonify(find_schedule(date)), HTTPStatus.OK


@app.route("/schedule/<date>/movies", methods=["GET"])
def get_schedule_movies(date: str):
    return jsonify(find_schedule(date)["movies"]), HTTPStatus.OK


@app.route("/schedule", methods=["POST"])
def add_schedule():
    entry = validate_payload(ScheduleInput, request.get_json())
    if any(str(e["date"]) == entry.date for e in schedule):
        raise ScheduleAlreadyExistsError()

    schedule.append(entry.model_dump())
    write(schedule)

    return jsonify(schedule[-1]), HTTPStatus.CREATED


@app.route("/schedule/<date>", methods=["DELETE"])
def delete_schedule(date: str):
    i = find_schedule_index(date)
    schedule.pop(i)
    write(schedule)
    return "", HTTPStatus.NO_CONTENT


if __name__ == "__main__":
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)

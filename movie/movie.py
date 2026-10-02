from http import HTTPStatus
from json import load, dump, loads
from datetime import datetime
from typing import Any, Type, TypeVar
from uuid import uuid4

from flask import Flask, jsonify, request
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)
from werkzeug.exceptions import HTTPException, NotFound, UnprocessableEntity

app = Flask(__name__)

PORT = 3200
HOST = '0.0.0.0'
DB_PATH = "./databases/movies.json"

with open(DB_PATH, 'r') as jsf:
    movies = load(jsf)["movies"]


def write(movies):
    with open(DB_PATH, 'w') as f:
        dump({"movies": movies}, f)


T = TypeVar("T", bound=BaseModel)


class MovieInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    title: str = Field(max_length=100)
    rating: int = Field(ge=0, le=10)
    director: str = Field(max_length=100)


class MovieResponse(BaseModel):
    id: str
    title: str
    rating: int
    director: str


def validate_payload(model: Type[T], payload: Any) -> T:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise UnprocessableEntity(description=loads(exc.json())) from exc


class MovieNotFoundError(NotFound):
    pass


@app.errorhandler(MovieNotFoundError)
def handle_movie_not_found(e: MovieNotFoundError):
    return jsonify(error="Movie does not exist"), 404


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    return jsonify(error=e.description), e.code


def find_movie(movieid: str) -> int:
    for i, movie in enumerate(movies):
        if str(movie["id"]) == str(movieid):
            return movies[i]
    raise MovieNotFoundError()

def find_movie_index(movieid: str) -> int:
    for i, movie in enumerate(movies):
        if str(movie["id"]) == str(movieid):
            return i
    raise MovieNotFoundError()


@app.route("/movies", methods=["GET"])
def get_movies():
    return jsonify(movies), HTTPStatus.OK


@app.route("/movies/<movieid>", methods=["GET"])
def get_movie_byid(movieid: str):
    return jsonify(find_movie(movieid)), HTTPStatus.OK


@app.route("/movies", methods=["POST"])
def add_movie():
    movie = validate_payload(MovieInput, request.get_json())
    movies.append({"id": str(uuid4()), **movie.model_dump()})
    write(movies)

    movie = movies[-1]
    return jsonify(movie), HTTPStatus.CREATED


@app.route("/movies/<movieid>", methods=["PUT"])
def update_movie(movieid: str):
    movie = validate_payload(MovieInput, request.get_json())
    i = find_movie_index(movieid)
    movies[i] = {"id": movies[i]["id"], **movie.model_dump()}
    write(movies)

    return jsonify(movies[i]), HTTPStatus.OK


@app.route("/movies/<movieid>", methods=["DELETE"])
def delete_movie(movieid: str):
    i = find_movie_index(movieid)
    movies.pop(i)
    write(movies)
    return "", HTTPStatus.NO_CONTENT


if __name__ == "__main__":
    #p = sys.argv[1]
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)

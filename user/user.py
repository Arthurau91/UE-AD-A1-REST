"""User API"""

import json

from flask import Flask, jsonify, make_response, request

from werkzeug.exceptions import NotFound

app = Flask(__name__)

PORT = 3203
HOST = '0.0.0.0'

with open('{}/databases/users.json'.format("."), "r", encoding="utf-8") as jsf:
    users = json.load(jsf)["users"]

@app.route("/", methods=['GET'])
def get_users():
    """get all users

    Returns:
        Json: A list of all users data
    """
    return jsonify({"users": users})

@app.route("/<user_id>", methods=['GET'])
def get_user(user_id):
    """get a single user by ID

    Args:
        user_id (int): The ID of the user to retrieve

    Raises:
        NotFound: If the user with the specified ID is not found

    Returns:
        dict: The user data if found
    """
    user = next((user for user in users if user["id"] == user_id), None)
    if user is None:
        raise NotFound(description="User not found")
    return jsonify(user)

@app.route("/", methods=['POST'])
def create_user():
    """Create a new user

    Returns:
        Json: Validation message and status code
    """
    data = request.get_json()
    if not data or "id" not in data or "name" not in data:
        return make_response(jsonify({"error": "Invalid user data"}), 400)

    if any(user["id"] == data["id"] for user in users):
        return make_response(jsonify({"error": "User with this ID already exists"}), 400)

    users.append(data)
    return make_response(jsonify({"message": "User created successfully"}), 201)

@app.route("/<user_id>", methods=['PUT'])
def update_user(user_id):
    """Update a user

    Args:
        user_id (int): The ID of the user to update

    Raises:
        NotFound: If the user with the specified ID is not found

    Returns:
        Json: Validation message and status code
    """
    user = next((user for user in users if user["id"] == user_id), None)
    if user is None:
        raise NotFound(description="User not found")
    data = request.get_json()
    if not data or "id" not in data or "name" not in data:
        return make_response(jsonify({"error": "Invalid user data"}), 400)
    users.remove(user)
    users.append(data)
    return make_response(jsonify({"message": "User updated successfully"}), 200)

@app.route("/<user_id>", methods=['DELETE'])
def delete_user(user_id):
    """User deletion

    Args:
        user_id (int): The ID of the user to delete

    Raises:
        NotFound: If the user with the specified ID is not found

    Returns:
        Json: Validation message and status code
    """
    user = next((user for user in users if user["id"] == user_id), None)
    if user is None:
        raise NotFound(description="User not found")
    users.remove(user)
    return make_response(jsonify({"message": "User deleted successfully"}), 200)

if __name__ == "__main__":
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)

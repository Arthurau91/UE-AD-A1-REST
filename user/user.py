"""User API"""

import json

from flask import Flask, jsonify, make_response

from werkzeug.exceptions import NotFound

app = Flask(__name__)

PORT = 3203
HOST = '0.0.0.0'

with open('{}/databases/users.json'.format("."), "r", encoding="utf-8") as jsf:
    users = json.load(jsf)["users"]

@app.route("/", methods=['GET'])
def home():
    return jsonify({"users": users})

@app.route("/<user_id>", methods=['GET'])
def get_user(user_id):
    user = next((user for user in users if user["id"] == user_id), None)
    if user is None:
        raise NotFound(description="User not found")
    return jsonify(user)

@app.route("/", methods=['POST'])
def create_user():
    pass

@app.route("/<user_id>", methods=['PUT'])
def update_user(user_id):
    user = next((user for user in users if user["id"] == user_id), None)
    if user is None:
        raise NotFound(description="User not found")
    pass

@app.route("/<user_id>", methods=['DELETE'])
def delete_user(user_id):
    user = next((user for user in users if user["id"] == user_id), None)
    if user is None:
        raise NotFound(description="User not found")
    users.remove(user)
    return make_response(jsonify({"message": "User deleted successfully"}), 200)

if __name__ == "__main__":
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)

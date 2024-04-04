from flask import Flask, render_template, request, jsonify, session, redirect
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
from os import getenv

MONGO_URI = getenv("MONGO_URI") 
SECRET_KEY = getenv("SECRET_KEY")

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
socketio = SocketIO(app)

client = MongoClient(MONGO_URI)
database = client["chat_app"]
collection = database["messages"]
users = database["users"]


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users.find_one({"username": username})
        if not user or not check_password_hash(user["password"], password):
            return jsonify(
                {"status": "fail", "message": "Incorrect username or password"}
            )

        session["username"] = username
        session["success"] = "Successfully logged in"
        return jsonify({"status": "success"})
    return render_template("login.html")


@app.route("/")
def index():
    if session.get("username", False):
        messages = collection.find()
        return render_template("index.html", messages=messages)
    return redirect("/login")


@socketio.on("send_message")
def handle_message(data):
    message = data["message"]
    sender = session["username"]
    collection.insert_one({"sender": sender, "message": message})
    emit("new_message", {"sender": sender, "message": message}, broadcast=True)


if __name__ == "__main__":
    socketio.run(app)

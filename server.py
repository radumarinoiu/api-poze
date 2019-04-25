import db
import json

from flask import Flask, request, jsonify, Response


# Flask Initialization
app = Flask(__name__)

@app.route("/albums", methods = ["GET"])
def get_all_albums():
    response = Response(status=200)
    response.json = jsonify(db.get_all_albums())
    return response

if __name__ == "__main__":
    print "Starting webserver..."
    app.run(host="0.0.0.0", port=5000)
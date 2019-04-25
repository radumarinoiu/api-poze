import db
import json

from flask import Flask, request, jsonify, Response


# Flask Initialization
app = Flask(__name__)

@app.route("/albums", methods = ["GET"])
def get_all_albums():
    return jsonify(db.get_all_albums()), 200

if __name__ == "__main__":
    print "Starting webserver..."
    app.run(host="0.0.0.0", port=5000)
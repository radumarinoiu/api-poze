import db
import json

from flask import Flask, request, jsonify, Response

# Flask Initialization
app = Flask(__name__)


# Helper Functions
def check_fields(obj, fields_to_check):
    for field in fields_to_check:
        if field not in obj:
            return False
        if not isinstance(obj[field], fields_to_check[field]):
            return False
    return True


# Routes
@app.route("/albums", methods = ["GET"])
def get_all_albums():
    return jsonify(db.get_all_albums()), 200

@app.route("/albums/<album_id>", methods = ["GET"])
def get_album(album_id):
    result = db.get_album(album_id)
    if result:
        return jsonify(result), 200
    return jsonify({}), 404

@app.route("/albums", methods = ["POST"])
def create_album():
    req_obj = request.json

    # Checks
    if not check_fields(req_obj, {"name": str, "description": str, "images": list}):
        return jsonify({}), 400
    # Checks

    album_id = db.create_album(req_obj["name"], req_obj["description"], req_obj["images"])
    return jsonify([album_id]), 200

@app.route("/albums/<album_id>", methods = ["DELETE"])
def delete_album(album_id):
    if db.delete_album(album_id):
        return jsonify({}), 200
    return jsonify({}), 404

@app.route("/albums/<album_id>/images", methods = ["GET"])
def get_images_from_album(album_id):
    image_list = db.get_images_from_album(album_id)
    if image_list is not None:
        return jsonify(image_list), 200
    return jsonify({}), 404

@app.route("/albums/<album_id>/images", methods = ["PUT"])
def add_images_to_album(album_id):
    req_obj = request.json

    # Checks
    if not check_fields(req_obj, {"image_ids": list}):
        return jsonify({}), 400
    # Checks

    db.add_images_to_album(album_id, req_obj["image_ids"])
    return jsonify({}), 200

@app.route("/albums/<album_id>/images", methods = ["DELETE"])
def remove_images_from_album(album_id):
    req_obj = request.json

    # Checks
    if not check_fields(req_obj, {"image_ids": list}):
        return jsonify({}), 400
    # Checks

    db.remove_images_from_album(album_id, req_obj["image_ids"])
    return jsonify({}), 200

@app.route("/albums/<album_id>/images/<image_id>", methods = ["GET"])
def get_image_from_album(album_id, image_id):  # Ik, it's wrong, idk rn
    image = db.get_image(image_id)
    if image:
        return jsonify(image), 200
    return jsonify({}), 404
        



@app.route("/images", methods = ["GET"])
def get_all_images():
    return jsonify(db.get_all_images()), 200

@app.route("/images/<image_id>", methods = ["GET"])
def get_image(image_id):
    image = db.get_image(image_id)
    if image:
        return jsonify(image), 200
    return jsonify({}), 404

@app.route("/images", methods = ["POST"])
def upload_images():
    req_obj = request.json()

    # Checks
    if not check_fields(req_obj, {"image_paths": list}):
        return jsonify({}), 400
    # Checks

    return jsonify(db.upload_images(req_obj["image_paths"])), 200


if __name__ == "__main__":
    print "Starting webserver..."
    app.run(host="0.0.0.0", port=5000)
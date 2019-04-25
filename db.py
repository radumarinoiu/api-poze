import os
import pymongo
import time

from pymongo import MongoClient
from bson.objectid import ObjectId
from imgurpython import ImgurClient

# MongoDB Initialization
MONGO_HOST = "localhost"
MONGO_DB = "tasks_db"  # TODO: To be removed
MONGO_USER = "devs"  # TODO: To be removed
MONGO_PASS = "devs"  # TODO: To be removed

######################### TO BE REMOVED #########################
# from sshtunnel import SSHTunnelForwarder
# SSH_SERVER = SSHTunnelForwarder(("192.168.0.20", 5120), ssh_username=MONGO_USER, ssh_password=MONGO_PASS, remote_bind_address=("127.0.0.1", 27017))
# SSH_SERVER.start()
# MONGO_CLIENT = MongoClient("127.0.0.1", SSH_SERVER.local_bind_port)
######################### TO BE REMOVED #########################

MONGO_CLIENT = MongoClient("mongodb://{}:{}@{}/{}".format(MONGO_USER, MONGO_PASS, MONGO_HOST, MONGO_DB)) # This is the right way
MONGO_DB_OBJ = MONGO_CLIENT["gallery_api"]
MONGO_COLL_IMAGES = MONGO_DB_OBJ["images"]
MONGO_COLL_ALBUMS = MONGO_DB_OBJ["albums"]

# ImgurAPI Initialization
CLIENT_ID = '972bd7815e751c4'  # TODO: To be removed
CLIENT_SECRET = '3cd24dd170f51f447b70ecc5187abad18a0aacf7'  # TODO: To be removed
CLIENT_INSTANCE = ImgurClient(CLIENT_ID, CLIENT_SECRET)


# Image Functions
def upload_images(images):
    image_ids = []
    for image in images:
        image_obj = CLIENT_INSTANCE.upload_from_path(image)
        if image_obj:
            image_obj["created_at"] = time.time()
            image_id = str(MONGO_COLL_IMAGES.insert_one(image_obj).inserted_id)
            image_ids.append(image_id)
    return image_ids

def get_all_images():
    all_image_ids = []
    for image in MONGO_COLL_IMAGES.find({}):
        all_image_ids.append(str(image["_id"]))
    return all_image_ids

def get_image_link_by_id(image_id):
    return MONGO_COLL_IMAGES.find_one({"_id": ObjectId(image_id)})["link"]


# Album Functions
def get_all_albums():
    all_album_ids = []
    for album in MONGO_COLL_ALBUMS.find({}):
        all_album_ids.append(str(album["_id"]))
    return all_album_ids

def get_album(album_id):
    album_obj = MONGO_COLL_ALBUMS.find_one({"_id": ObjectId(album_id)})
    album_obj["_id"] = str(album_obj["_id"])
    return album_obj

def create_album(name, description="", image_ids=[]):
    return str(MONGO_COLL_ALBUMS.insert_one({"name": name, "description": description, "images": image_ids, "created_at": time.time(), "modified_at": time.time()}).inserted_id)

def delete_album(album_id):
    MONGO_COLL_ALBUMS.delete_one({"_id": ObjectId(album_id)})
    return True

def get_all_image_ids_from_album(album_id):
    return MONGO_COLL_ALBUMS.find_one({"_id": ObjectId(album_id)})["images"]

def get_all_image_links_from_album(album_id):
    image_ids_list = MONGO_COLL_ALBUMS.find_one({"_id": ObjectId(album_id)})["images"]
    return [get_image_link_by_id(image_id) for image_id in image_ids_list]

def add_photos_to_album(album_id, image_ids=[]):
    album = MONGO_COLL_ALBUMS.find_one({"_id": ObjectId(album_id)})
    album["images"] += image_ids
    MONGO_COLL_ALBUMS.update(
        {"_id": ObjectId(album_id)},
        {"$set": {"images": album["images"], "modified_at": time.time()}},
        upsert=False)
    return album_id

def remove_photos_from_album(album_id, image_ids=[]):
    album = MONGO_COLL_ALBUMS.find_one({"_id": ObjectId(album_id)})
    for image_id in image_ids:
        album["images"].remove(image_id)
    MONGO_COLL_ALBUMS.update(
        {"_id": ObjectId(album_id)},
        {"$set": {"images": album["images"], "modified_at": time.time()}},
        upsert=False)
    return album_id


# Main
def main():
    pass

    # dir_list = [os.path.join(r"C:\Users\raduc\Pictures\Samples", image) for image in os.listdir(r"C:\Users\raduc\Pictures\Samples")]
    # to_upload_list = []
    # for img in dir_list:
    #     if os.path.isfile(img):
    #         to_upload_list.append(img)
    # id_list = upload_images(to_upload_list)

    # Test Albums
    # album_id = create_album("Test Album 2", description="test")
    # print get_album(album_id)
    # add_photos_to_album(album_id, ["5cc1ff20c7f269bdd79b4ab0", "5cc1ff52ef105c3dfba16b99"])
    # print get_album(album_id)
    # print get_all_image_ids_from_album(album_id)
    # print get_all_image_links_from_album(album_id)
    # remove_photos_from_album(album_id, ["5cc1ff52ef105c3dfba16b99"])
    # print get_album(album_id)
    # delete_album(album_id)

if __name__=="__main__":
    main()

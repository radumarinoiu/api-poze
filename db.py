import os
import time
import shutil
import pymongo
import logging
import requests
import traceback

from threading import Thread, Lock
from pymongo import MongoClient
from bson.objectid import ObjectId
from imgurpython import ImgurClient, helpers as ImgurHelpers

# Constants
TEMP_STORAGE_FOLDER = r"D:\temp"
UPLOADS_PER_HOUR = 50

# Generic Initialization
logging.basicConfig()
if not os.path.exists(TEMP_STORAGE_FOLDER):
    os.makedirs(TEMP_STORAGE_FOLDER)


# MongoDB Initialization
MONGO_HOST = "localhost"
MONGO_DB = "tasks_db"  # TODO: To be removed
MONGO_USER = "devs"  # TODO: To be removed
MONGO_PASS = "devs"  # TODO: To be removed

######################### TO BE REMOVED #########################
from sshtunnel import SSHTunnelForwarder
SSH_SERVER = SSHTunnelForwarder(("192.168.0.20", 5120), ssh_username=MONGO_USER, ssh_password=MONGO_PASS, remote_bind_address=("127.0.0.1", 27017))
SSH_SERVER.start()
MONGO_CLIENT = MongoClient("127.0.0.1", SSH_SERVER.local_bind_port)
######################### TO BE REMOVED #########################


# MONGO_CLIENT = MongoClient("mongodb://{}:{}@{}/{}".format(MONGO_USER, MONGO_PASS, MONGO_HOST, MONGO_DB)) # This is the right way
MONGO_DB_OBJ = MONGO_CLIENT["gallery_api"]
MONGO_COLL_IMAGES = MONGO_DB_OBJ["images"]
MONGO_COLL_UPLOAD_QUEUE = MONGO_DB_OBJ["upload_queue"]
MONGO_COLL_ALBUMS = MONGO_DB_OBJ["albums"]
MONGO_COLL_SYSTEM = MONGO_DB_OBJ["system"]


# ImgurAPI Initialization
CLIENT_ID = '972bd7815e751c4'  # TODO: To be removed
CLIENT_SECRET = '3cd24dd170f51f447b70ecc5187abad18a0aacf7'  # TODO: To be removed
CLIENT_INSTANCE = ImgurClient(CLIENT_ID, CLIENT_SECRET)


# Image Functions
def upload_image_by_path(image_path):
    image_obj = CLIENT_INSTANCE.upload_from_path(image_path, anon=False)
    if image_obj:
        image_id = str(MONGO_COLL_IMAGES.insert_one(image_obj).inserted_id)
        return image_id
    

# def upload_images_by_url(image_urls):
#     image_ids = []
#     for image_url in image_urls:
#         image_obj = CLIENT_INSTANCE.upload_from_url(image_url)
#         if image_obj:
#             image_obj["created_at"] = time.time()
#             image_id = str(MONGO_COLL_IMAGES.insert_one(image_obj).inserted_id)
#             image_ids.append(image_id)
#     return image_ids

def get_all_images():
    all_images = list(MONGO_COLL_IMAGES.find({}))
    for image in all_images:
        image["_id"] = str(image["_id"])
        image.pop("deletehash")
    return all_images

def get_image(image_id):
    image = MONGO_COLL_IMAGES.find_one({"_id": ObjectId(image_id)})
    if image:
        image["_id"] = str(image["_id"])
        image.pop("deletehash")
        return image
    return None

def add_images_to_queue_by_path(image_paths):
    image_ids = []
    for image_path in image_paths:
        name, ext = os.path.splitext(os.path.basename(image_path))
        new_filename = "{name}_{uid}{ext}".format(name=name, uid=time.time(), ext=ext)
        time.sleep(0.1)
        shutil.copyfile(image_path, os.path.join(TEMP_STORAGE_FOLDER, new_filename))
        image_ids.append(str(MONGO_COLL_UPLOAD_QUEUE.insert_one({"path": os.path.join(TEMP_STORAGE_FOLDER, new_filename), "added_at": time.time()}).inserted_id))
    return image_ids

def add_images_to_queue_by_url(image_urls):
    image_ids = []
    for image_url in image_urls:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        if "image/jpeg" in response.headers['content-type'] or "image/png" in response.headers['content-type']:
            name, ext = os.path.splitext(os.path.basename(image_url))
            new_filename = "{name}_{uid}{ext}".format(name=name, uid=time.time(), ext=ext)
            time.sleep(0.1)
            with open(os.path.join(TEMP_STORAGE_FOLDER, new_filename), 'wb') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)
            MONGO_COLL_UPLOAD_QUEUE.insert_one({"path": os.path.join(TEMP_STORAGE_FOLDER, new_filename), "added_at": time.time()})
    return image_ids

def auto_upload_images_from_queue():
    while True:
        print "Uploading images from queue..."
        try:
            images_ready_to_upload = list(MONGO_COLL_UPLOAD_QUEUE.find({}).sort("added_at", 1).limit(check_available_uploads()))
            for image_upload_obj in images_ready_to_upload:
                print("Uploading {}".format(os.path.basename(image_upload_obj["path"])))
                try:
                    upload_image_by_path(image_upload_obj["path"])
                except ImgurHelpers.error.ImgurClientRateLimitError:
                    print("Rate-Limit Exceeded, stopping upload.\n{}").format(traceback.format_exc())
                    break
                except IOError, e:
                    if e.errno==2:
                        print("Image file is missing, considering it invalid and continuing.")
                except Exception:
                    print("Unknown failure, stopping upload.\n{}".format(traceback.format_exc()))
                    break

                try:
                    os.remove(image_upload_obj["path"])
                except (IOError, WindowsError):
                    print("Image file is missing or cannot be deleted, continuing.\n{}".format(traceback.format_exc()))

                MONGO_COLL_UPLOAD_QUEUE.delete_one({"_id": image_upload_obj["_id"]})
            uploads_left = check_available_uploads()
            if uploads_left:
                print("Uploads left: {}".format(uploads_left))
                logging.info("Uploads left: {}".format(uploads_left))
                time.sleep(10)
            else:
                limit_expiry_time = check_available_uploads_reset_time()-time.time()+10
                print("Upload limit reached, waiting until the limit expires. ({}s)".format(limit_expiry_time))
                logging.info("Upload limit reached, waiting until the limit expires. ({}s)".format(limit_expiry_time))
                time.sleep(limit_expiry_time)
        except (KeyboardInterrupt, SystemExit):
            break
        except Exception:
            print("Failed to upload images from queue, retrying at next upload.\n{}".format(traceback.format_exc()))
            logging.error("Failed to upload images from queue, retrying at next upload.\n{}".format(traceback.format_exc()))
            time.sleep(10)


# Album Functions
def get_all_albums():
    all_album_ids = []
    for album in MONGO_COLL_ALBUMS.find({}):
        all_album_ids.append(str(album["_id"]))
    return all_album_ids

def get_album(album_id):
    album_obj = MONGO_COLL_ALBUMS.find_one({"_id": ObjectId(album_id)})
    if album_obj:
        album_obj["_id"] = str(album_obj["_id"])
        return album_obj
    return None

def create_album(name, description, image_ids):
    return str(MONGO_COLL_ALBUMS.insert_one({"name": name, "description": description, "images": image_ids, "created_at": time.time(), "modified_at": time.time()}).inserted_id)

def delete_album(album_id):
    return MONGO_COLL_ALBUMS.delete_one({"_id": ObjectId(album_id)}).deleted_count

def get_images_from_album(album_id):
    album = MONGO_COLL_ALBUMS.find_one({"_id": ObjectId(album_id)})
    if album:
        image_ids_list = list(MONGO_COLL_ALBUMS.find_one({"_id": ObjectId(album_id)})["images"])
        return [get_image(image_id) for image_id in image_ids_list]
    return None

def add_images_to_album(album_id, image_ids):
    album = MONGO_COLL_ALBUMS.find_one({"_id": ObjectId(album_id)})
    album["images"] += image_ids
    MONGO_COLL_ALBUMS.update(
        {"_id": ObjectId(album_id)},
        {"$set": {"images": album["images"], "modified_at": time.time()}},
        upsert=False)
    return True

def remove_images_from_album(album_id, image_ids):
    album = MONGO_COLL_ALBUMS.find_one({"_id": ObjectId(album_id)})
    for image_id in image_ids:
        album["images"].remove(image_id)
    MONGO_COLL_ALBUMS.update(
        {"_id": ObjectId(album_id)},
        {"$set": {"images": album["images"], "modified_at": time.time()}},
        upsert=False)
    return album_id


# System Functions
def check_available_uploads():
    # uploads_last_hour = MONGO_COLL_IMAGES.find({"datetime": {"$gte":check_available_uploads_reset_time()-3600}}).count()
    # return UPLOADS_PER_HOUR - uploads_last_hour

    # BUG: THIS SHOULD ONLY BE USED IF THERE ARE NO OTHER
    # POST REQUESTS SENT TO IMGUR EXCEPTING PHOTO UPLOADS!!!
    # OTHERWISE, USE ABOVE FUNCTION!!
    usercredits = CLIENT_INSTANCE.get_credits()
    return min(usercredits["UserRemaining"]-usercredits["UserLimit"] + UPLOADS_PER_HOUR, usercredits["ClientRemaining"])

def check_available_uploads_reset_time():
    usercredits = CLIENT_INSTANCE.get_credits()
    return usercredits["UserReset"]


# Main
def main():
    # MONGO_COLL_UPLOAD_QUEUE.delete_many({})
    # dir_list = [os.path.join(r"C:\Users\raduc\Pictures\Samples", image) for image in os.listdir(r"C:\Users\raduc\Pictures\Samples")]
    # to_upload_list = []
    # for img in dir_list:
    #     if os.path.isfile(img):
    #         to_upload_list.append(img)
    #         to_upload_list.append(img)
    #         to_upload_list.append(img)
    #         to_upload_list.append(img)
    #         to_upload_list.append(img)
    # add_images_to_queue_by_path(to_upload_list)
    pass


# Scheduler Initialization
BACKGROUND_EVENT_THREAD = Thread(target=auto_upload_images_from_queue)
BACKGROUND_EVENT_THREAD.start()

if __name__=="__main__":
    main()
    BACKGROUND_EVENT_THREAD.join()

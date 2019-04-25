# ASII Gallery REST API
ASII Gallery is a REST API that provides an easy interface for storing photos in the cloud.
### Usage:

| Method | Route | Action |
| ------ | ------ | ------ |
| GET | /albums | Get all album ids |
| GET | /albums/`album_id` | Get album with id `album_id` |
| GET | /albums/`album_id`/images | Get ids for all images in album with id `album_id` |
| GET | /albums/`album_id`/images/`image_id` | Get image with id `image_id` from album with id `album_id` |
|  |  |  |
| POST | /albums | Creates a new album using json `{"name": str, "description": str, "images": list}` and returns it's id |
|  |  |  |
| PUT | /albums/`album_id`/images | Add images to album with id `album_id` using json `{"image_ids": list}` |
|  |  |  |
| DELETE | /albums/`album_id` | Delete album with id `album_id` |
| DELETE | /albums/`album_id`/images | Remove images from album with id `album_id` using json `{"image_ids": list}` |

| Method | Route | Action |
| ------ | ------ | ------ |
| GET | /images | Get all image ids |
| GET | /images/`image_id` | Get image with id `image_id` |
|  |  |  |
| POST | /images | Upload images using json `{"image_paths": list}` returning a list of their ids |

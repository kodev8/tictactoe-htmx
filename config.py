import os
from dotenv import load_dotenv

load_dotenv()

# FLASK
SECRET_KEY = os.getenv('SECRET_KEY')

# DB CONFIG
DB_URL = os.getenv('DB_URL')

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')

# FILE TYPES
class Files:
    IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'heic'}
    VIDEO_EXTS = {'mp4', 'mov', 'avi'}
    GIF_EXTS = {'gif'}

    MEDIA_EXTS = IMAGE_EXTS.union(VIDEO_EXTS)
    ALL_EXTS = MEDIA_EXTS.union(GIF_EXTS)

    MAP = {
        'image': {
            'exts':IMAGE_EXTS,
            'pre':'image'
            },
        'video': {
            'exts': VIDEO_EXTS,
            'pre':'video'
            },
        'gif': {
            'exts': GIF_EXTS,
            'pre':'image'
        }
    }

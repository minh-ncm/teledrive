import os


FILE_MAX_SIZE = 1024 * 1024 * 1000 # 1GB

LOCAL_WORK_DIR = "files"
LOCAL_UPLOAD_DIR = os.path.join(LOCAL_WORK_DIR, "upload")
LOCAL_DOWNLOAD_DIR = os.path.join(LOCAL_WORK_DIR, "download")

LOCAL_TEMP_DIR = "tmp"

FILE_NAME_CONFIG = "config.json"
FILE_NAME_UPLOAD = "upload.json"
FILE_NAME_DOWNLOAD = "download.json"
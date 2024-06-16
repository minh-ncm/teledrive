import os


# FILE_MAX_SIZE = 2_097_152_000 # 2GB
FILE_MAX_SIZE = 100

LOCAL_WORK_DIR = "files"
LOCAL_UPLOAD_DIR = os.path.join(LOCAL_WORK_DIR, "upload")
LOCAL_DOWNLOAD_DIR = os.path.join(LOCAL_WORK_DIR, "download")

LOCAL_TEMP_DIR = "tmp"
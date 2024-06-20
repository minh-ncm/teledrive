from pydantic_settings import BaseSettings
from pydantic import BaseModel, RootModel
import json
from typing import List
from constants import FILE_NAME_CONFIG, FILE_NAME_UPLOAD, FILE_NAME_DOWNLOAD


class Settings(BaseSettings):
    API_APP_ID: int
    API_APP_HASH: str
    CHAT_ID: int

class UploadInfo(BaseModel):
    path: str
    namespace: str

class UploadList(RootModel):
    root: List[UploadInfo]


class DownloadInfo(BaseModel):
    og_name: str
    namespace: str


class DownloadList(RootModel):
    root: List[DownloadInfo]


# settings = Settings(_env_file=".env")
settings = Settings.model_validate(json.load(open(FILE_NAME_CONFIG)))
upload_list =  UploadList.model_validate(json.load(open(FILE_NAME_UPLOAD))).root
download_list = DownloadList.model_validate(json.load(open(FILE_NAME_DOWNLOAD))).root
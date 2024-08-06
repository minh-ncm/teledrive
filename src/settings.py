# -*- coding: utf-8 -*-
import json
import os
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings

from constants import FILE_NAME_CONFIG


class Settings(BaseSettings):
    model_config = ConfigDict(extra="ignore")
    API_APP_ID: Optional[int] = None
    API_APP_HASH: Optional[str] = None
    CHAT_ID: Optional[int] = None


class DownloadInfo(BaseModel):
    og_name: str
    namespace: str


if not os.path.exists(FILE_NAME_CONFIG):
    settings = None
else:
    settings = Settings.model_validate(json.load(open(FILE_NAME_CONFIG)))

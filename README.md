# Overview
Teledrive is a versatile application that facilitates the upload and download of files and folders between Telegram and your local host. Uploaded files are tracked in an SQLite database for easy management and retrieval. Large files are split into multiple parts for uploading and are seamlessly rejoined during the download process.

# Installation
### Download executeable file
### Create executeable yourself
`pyinstaller -y --noconsole src/main.py`

# ROADMAP
- [] Chose CHAT ID ony first time setup
- [] Clean up code
- [] Handle progress bar cancel action
- [] Enhace UI
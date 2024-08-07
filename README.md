# Overview
Teledrive is a versatile application that facilitates the upload and download of files and folders between Telegram and your local host. Uploaded files are tracked in an SQLite database for easy management and retrieval. Large files are split into multiple parts for uploading and are seamlessly rejoined during the download process.

# Installation
### Download executeable file
- Go to [releases](https://github.com/minh-ncm/teledrive/releases) pages and download `teledrive.zip`

### Create executeable yourself
If you want to customize the source code and create an executable file just run the following command: `pyinstaller -y --noconsole src/teledrive.py`

# User guide
1. Create your API ID and API hash
- [Login to your Telegram account](https://my.telegram.org/) with the phone number of the developer account to use.
- Click under API Development tools.
- A Create new application window will appear. Fill in your application details. There is no need to enter any URL, and only the first two fields (App title and Short name) can currently be changed later.
- Click on Create application at the end. Remember that your API hash is secret and Telegram won’t let you revoke it. Don’t post it anywhere!

2. Setting up Teledrive
- After click on the `teledrive.exe`, click on `Set up API`
- Enter your API ID and API Hash you just created on the previous step
- Enter your phone (international format). Then click `Send code`
- Enter the login code you receive from Telegram for verification and login

3. Uploading
- Click at upload on the menu bar and select files you want to backup
- Enter the namespace. This will act download location with root from the download folder
# ROADMAP
- [] Clean up code
- [] Handle progress bar cancel actions
- [] Enhance UI
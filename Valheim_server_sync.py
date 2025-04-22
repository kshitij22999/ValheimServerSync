# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 11:20:00 2025

@author: monk
"""

import os
from datetime import datetime, timezone, timedelta
from Google import Create_Service
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

CLIENT_SECRET_FILE = 'client_secret.json'
API_NAME='DRIVE'
API_VERSION='v3'
SCOPE=['https://www.googleapis.com/auth/drive']
FOLDERID = '1MxITvBTBylZ9zv_2pzjrigaDKidl2ocL'
MIME_TYPE='text/plain'
FILEID = ''


service = Create_Service(CLIENT_SECRET_FILE,API_NAME,API_VERSION,SCOPE)

def convert_utc_to_ist(utc_timestamp):
    # Convert ISO 8601 string to datetime object (UTC)
    utc_time = datetime.fromisoformat(utc_timestamp.replace("Z", "+00:00"))
    
    # Define IST timezone (UTC+5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = utc_time.astimezone(timezone(ist_offset))
    
    # Convert back to ISO format with 'Z' replaced by '+05:30'
    return ist_time.isoformat(timespec='milliseconds').replace("+05:30", "Z")

def get_server_modified_time(folder,filename):
    mod_time = os.path.getmtime(folder+filename)
    formatted_time = datetime.fromtimestamp(mod_time)
    print(f"Last modified time: {formatted_time}")
    return formatted_time
    
def get_drive_server_modified_time(fileid):
    try:
        file_metadata = service.files().get(
            fileId=fileid,
            fields="id, name, modifiedTime"
        ).execute()
        
        return datetime.fromisoformat(convert_utc_to_ist(file_metadata["modifiedTime"]).replace("Z", ""))
    
    except Exception as e:
        print(f"Error: {e}")
        return None

def file_upload(folder, filename):
    file_metadata = {
        'name':filename,
        'parents':[FOLDERID]
    }
    
    media = MediaFileUpload(folder+filename, mimetype=MIME_TYPE)
    
    respo = service.files().create(
        body = file_metadata,
        media_body = media,
        fields = 'id'
    ).execute()
    
    FILEID = respo.get('id')
    
def get_fileid(filename):
    try:
        results = service.files().list(
            q=f"name='{filename}' and '{FOLDERID}' in parents and trashed=false",
            spaces="drive",
            fields="files(id, name, mimeType)"
        ).execute()

        files = results.get("files", [])
        if not files:
            return None
        else:
            for file in files:
                FILEID = file['id']
        return FILEID
    
    except Exception as e:
        print(f"Error: {e}")
    
def datetime_comparer(drive_timestamp, local_timestamp):
    return local_timestamp > drive_timestamp

def empty_folder(folderId):
    try:
        # Step 1: List all files inside the folder
        results = service.files().list(
            q=f"'{folderId}' in parents and trashed=false",
            fields="files(id, name)"
        ).execute()

        files = results.get("files", [])

        if not files:
            print("Folder is already empty.")
            return
        
        # Step 2: Delete each file one by one
        for file in files:
            try:
                service.files().delete(fileId=file["id"]).execute()
                print(f"Deleted: {file['name']} (ID: {file['id']})")
            except Exception as e:
                print(f"Failed to delete {file['name']}: {e}")

        print("All files deleted successfully.")

    except Exception as e:
        print(f"Error: {e}")
    
def download_server_file(folder_id, local_path):
    try:
        # Step 1: List all files in the Google Drive folder
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name)"
        ).execute()

        files = results.get("files", [])

        if not files:
            print("No files found in the Drive folder.")
            return
        
        # Step 2: Download each file and replace the local one
        for file in files:
            file_id = file["id"]
            file_name = file["name"]
            local_file_path = os.path.join(local_path, file_name)

            try:
                # Request to download file
                request = service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)

                done = False
                while not done:
                    _, done = downloader.next_chunk()

                # Save file locally, replacing the existing one
                with open(local_file_path, "wb") as f:
                    f.write(fh.getvalue())

                print(f"Replaced: {local_file_path}")

            except Exception as e:
                print(f"Failed to download {file_name}: {e}")

    except Exception as e:
        print(f"Error: {e}")

def script(folder, filename):
    file_id = get_fileid(filename)
    if file_id is not None:
        if (datetime_comparer(get_drive_server_modified_time(file_id),get_server_modified_time(folder, filename))):
            empty_folder(FOLDERID)
            file_upload(folder, filename)
        else:
            download_server_file(FOLDERID, folder)
            print('download')
    else:
        file_upload(folder, filename)
        
if __name__ == '__main__':
    folder = 'C:\\Users\\admin\Desktop\\'
    filename = 'demofile.txt'
    
    file_id = get_fileid(filename)
    script(folder, filename)
    
    
    exit
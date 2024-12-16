import os
import subprocess
import shutil
import tempfile  # Import tempfile for creating temporary directories
import pandas as pd  # Import pandas to read the Excel file
import re  # Regular expression to match comments in markdown files
from urllib.parse import quote
from wiki_migrate_get_db import db_get_wiki
db_get_wiki()
# Define file path for the Excel file
EXCEL_FILE = "wiki_migrate_input.xlsx"

def encode_url_component(component):
    return quote(component, safe='')

# Function to read the Excel file and extract data
def read_excel_data(file_path):
    """Reads the Excel file and extracts relevant data."""
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)

        # Drop rows where any of the essential fields are null
        df.dropna(subset=['source_server_url', 'target_organization_url', 'source_project_name', 'target_project_name'
                                          ], inplace=True)
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        raise

def run_command(command, cwd=None, env=None):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True, env=env)
        print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        raise

def clone_on_prem_repo(on_prem_repo, source_username, source_password, clone_dir, wiki_source_project_name):
    """Clone the on-prem repository using provided credentials."""
    print(f"Cloning on-premise wiki repository from {on_prem_repo}...")
    # Construct the repository URL with credentials for authentication
    source_password
    auth_on_prem_repo = f"http://{source_username}:{source_password}@{on_prem_repo[7:]}/{wiki_source_project_name}/_git/{wiki_source_project_name}.wiki"
    print("testing", auth_on_prem_repo)

    run_command(["git", "clone", "--mirror", auth_on_prem_repo, clone_dir])
    print("Successfully cloned on-premise repository.")

def set_cloud_repo(cloud_repo, target_username, target_password, clone_dir, wiki_target_project_name):
    """Set the cloud repository as the new origin using provided credentials."""
    print(f"Setting cloud repository {cloud_repo} as the new origin...")
    # Construct the repository URL with credentials for authentication
    auth_cloud_repo = f"https://{target_username}:{target_password}@{cloud_repo[8:]}/{wiki_target_project_name}/_git/{wiki_target_project_name}_wiki"
    print("this",auth_cloud_repo)
    run_command(["git", "remote", "set-url", "origin", auth_cloud_repo], cwd=clone_dir)
    print("Cloud repository URL set as origin.")

def push_to_cloud_repo(clone_dir):
    """Push the repository to the cloud."""
    print("Pushing contents to the cloud repository...")
    run_command(["git", "push", "--mirror"], cwd=clone_dir)
    print("Successfully pushed wiki to cloud repository.")

def migrate_comments(clone_dir):
    """Migrate comments from the markdown files in the source repository to the cloud repository."""
    print("Migrating comments...")

    # Define a regex pattern to match comments in markdown files (HTML-style comments)
    comment_pattern = re.compile(r"<!--(.*?)-->", re.DOTALL)

    # Loop through all markdown files in the repository
    for root, dirs, files in os.walk(clone_dir):
        for file in files:
            if file.endswith(".md"):  # Only process markdown files
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find all comments using the regex pattern
                comments = comment_pattern.findall(content)

                if comments:
                    print(f"Found comments in {file}:")
                    for comment in comments:
                        print(f"- {comment}")

                # After processing, save the unchanged content (including comments) back
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)


def main():
    try:
        # Read inputs from the Excel file
        df = read_excel_data(EXCEL_FILE)
        source_username = input("Source Username: ").strip()
        source_password = input("Source Password: ").strip()
        target_username = input("Target Username: ").strip()
        target_password = input("Target Password: ").strip()

        for index, row in df.iterrows():
            print(f"Processing migration for row {index + 1}...")

            try:
                # Extract data for the current row
                on_prem_repo = row['source_server_url']
                cloud_repo = row['target_organization_url']
                wiki_source_project_name = row['source_project_name']
                wiki_target_project_name = row['target_project_name']

                # Encode the source password
                encoded_source_password = encode_url_component(source_password)

                # Create a temporary directory for cloning
                with tempfile.TemporaryDirectory() as clone_dir:
                    print(f"Using temporary directory: {clone_dir}")

                    # Perform migration steps
                    clone_on_prem_repo(on_prem_repo, source_username, encoded_source_password, clone_dir, wiki_source_project_name)
                    migrate_comments(clone_dir)  # Migrate comments from markdown files
                    set_cloud_repo(cloud_repo, target_username, target_password, clone_dir, wiki_target_project_name)
                    push_to_cloud_repo(clone_dir)

                print(f"Migration for row {index + 1} completed successfully.\n")

            except Exception as row_error:
                print(f"Error processing row {index + 1}: {row_error}")
                print("Skipping to the next row...\n")

    except Exception as e:
        print(f"Migration process failed: {e}")

if __name__ == "__main__":
    main()

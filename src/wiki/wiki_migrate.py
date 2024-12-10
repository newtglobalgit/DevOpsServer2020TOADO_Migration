import os
import subprocess
import shutil
import tempfile  # Import tempfile for creating temporary directories
import pandas as pd  # Import pandas to read the Excel file
import re  # Regular expression to match comments in markdown files

# Define file path for the Excel file
EXCEL_FILE = "wiki_migrate_input.xlsx"

# Function to read the Excel file and extract data
def read_excel_data(file_path):
    """Reads the Excel file and extracts relevant data."""
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)

        # Drop rows where any of the essential fields are null
        df.dropna(subset=['Source URL', 'Target URL', 'Source Project Name', 'Target Project Name',
                          'Source Username', 'Source Password', 'Target Username', 'Target Password'], inplace=True)
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
    auth_on_prem_repo = f"http://{source_username}:{source_password}@{on_prem_repo[7:]}/{wiki_source_project_name}/_git/{wiki_source_project_name}.wiki"
    print("testing", auth_on_prem_repo)

    run_command(["git", "clone", "--mirror", auth_on_prem_repo, clone_dir])
    print("Successfully cloned on-premise repository.")

def set_cloud_repo(cloud_repo, target_username, target_password, clone_dir, wiki_target_project_name):
    """Set the cloud repository as the new origin using provided credentials."""
    print(f"Setting cloud repository {cloud_repo} as the new origin...")
    # Construct the repository URL with credentials for authentication
    auth_cloud_repo = f"https://{target_username}:{target_password}@{cloud_repo[8:]}/{wiki_target_project_name}/_git/{wiki_target_project_name}.wiki"
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

        for index, row in df.iterrows():
            print(f"Processing migration for row {index + 1}...")

            on_prem_repo = row['Source URL']
            cloud_repo = row['Target URL']
            wiki_source_project_name = row['Source Project Name']
            wiki_target_project_name = row['Target Project Name']
            source_username = row['Source Username']
            source_password = row['Source Password']
            target_username = row['Target Username']
            target_password = row['Target Password']

            # Create a temporary directory
            with tempfile.TemporaryDirectory() as clone_dir:
                print(f"Using temporary directory: {clone_dir}")

                # Perform migration steps
                clone_on_prem_repo(on_prem_repo, source_username, source_password, clone_dir, wiki_source_project_name)
                migrate_comments(clone_dir)  # Migrate comments from markdown files
                set_cloud_repo(cloud_repo, target_username, target_password, clone_dir, wiki_target_project_name)
                push_to_cloud_repo(clone_dir)

            print(f"Migration for row {index + 1} completed successfully.\n")

    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    main()

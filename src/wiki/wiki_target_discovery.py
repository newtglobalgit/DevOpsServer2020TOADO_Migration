import os
from datetime import datetime
import openpyxl
import tempfile
import shutil
from urllib.parse import quote
import time
import subprocess
import pytz
import sys

# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.wiki.wiki_target_db import db_post_wiki
from src.wiki.wiki_target_db import db_get_wiki


def encode_url_component(component):
    return quote(component, safe='')


def get_last_modified_date_from_git(file_path, repo_dir):
    """
    Get the last commit date for a file in the Git repository.
    """
    try:
        # Run the git log command to get the last commit date for the file
        command = ["git", "log", "-1", "--format=%cd", file_path]
        result = subprocess.run(command, cwd=repo_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Get the commit date from the output (format: Mon Nov 23 14:38:56 2020 +0000)
            commit_date_str = result.stdout.strip()
            # Convert to datetime object
            last_modified = datetime.strptime(commit_date_str, "%a %b %d %H:%M:%S %Y %z")
            
            # Convert to IST (Indian Standard Time)
            ist = pytz.timezone('Asia/Kolkata')
            last_modified = last_modified.astimezone(ist)
            return last_modified.strftime('%Y-%m-%d %H:%M:%S')
        else:
            print(f"Error fetching last commit date for {file_path}: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error executing git log for {file_path}: {e}")
        return None


def clone_wiki_repo(auth_clone_url):
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"Cloning repository from {auth_clone_url} into {temp_dir}...")
        command = f"git clone {auth_clone_url} {temp_dir}"
        process = os.popen(command)
        output = process.read()
        process.close()
        if "fatal:" in output or "error:" in output:
            print(f"Error during git clone: {output}")
            return None
        else:
            print(f"Repository successfully cloned into {temp_dir}")
            return temp_dir
    except Exception as e:
        print(f"Error during git clone: {e}")
        return None


def discover_wiki_pages(wiki_repo_path):
    markdown_files = []
    for root, _, files in os.walk(wiki_repo_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, wiki_repo_path)
                
                # Get the last modified date using Git
                last_modified = get_last_modified_date_from_git(relative_path, wiki_repo_path)
                
                if last_modified:
                    file_size = os.path.getsize(file_path)
                    markdown_files.append((relative_path, file_size, last_modified))
    
    return markdown_files


def handle_remove_readonly(func, path, excinfo):
    try:
        os.chmod(path, 0o777)  # Change the file mode to make it writable
        func(path)  # Retry the removal of the file
    except Exception as e:
        print(f"Error removing {path}: {e}")


def main():
    input_file = "wiki_migrate_input.xlsx"
    
    username = input("Enter your username: ").strip()  
    password = input("Enter your Password: ").strip()  
    encoded_password = encode_url_component(password)

    # Load the input Excel file
    wb_input = openpyxl.load_workbook(input_file)
    ws_input = wb_input.active
    
    for row in range(2, ws_input.max_row + 1):
        # Read data from the Excel file
        server_url = ws_input.cell(row=row, column=5).value.strip() if ws_input.cell(row=row, column=5).value else ''
        project_name = ws_input.cell(row=row, column=6).value.strip() if ws_input.cell(row=row, column=6).value else ''
        wiki_path = f"{project_name}.wiki"
        
        if not server_url or not project_name or not wiki_path:
            print(f"Skipping row {row}: missing necessary data.")
            continue
        
        # Construct the URL for cloning
        break_down = server_url.split('/')
        clone_url = f"https://{break_down[-1]}@{break_down[-2]}/{break_down[-1]}/{project_name}/_git/{wiki_path}"
        print(clone_url)
        aut_url = f"{server_url}/{project_name}/_git/{wiki_path}"
        auth_clone_url = aut_url.replace("://", f"://{username}:{encoded_password}@")
        print("this is the auth",auth_clone_url)
        
        # Cloning and processing the wiki
        temp_dir = clone_wiki_repo(auth_clone_url)
        if temp_dir:
            wiki_pages = discover_wiki_pages(temp_dir)
            if wiki_pages:
                for file in wiki_pages:
                    file_path, size, modified = file
                    
                    # Create a data dictionary for the db_post_wiki function
                    data = {
                        "project_name": project_name,
                        "file_path": file_path,
                        "size_bytes": size,
                        "last_modified": modified,
                    }
                    
                    # Call db_post_wiki to save the data in the database
                    try:
                        db_post_wiki(data)
                        print("pppp",db_get_wiki())

                        print(f"Data successfully written to the database: {data}")
                    except Exception as e:
                        print(f"Error writing to database for file {file_path}: {e}")
            else:
                print(f"No wiki pages found for project: {project_name}.")
            
            time.sleep(1)
            shutil.rmtree(temp_dir, onerror=handle_remove_readonly)
            print(f"Temporary directory {temp_dir} cleaned up.")
        else:
            print(f"Failed to clone the repository for project {project_name}. Skipping.")
    
    print("All data has been processed and written to the database.")


if __name__ == "__main__":
    main()

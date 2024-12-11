import os
from datetime import datetime, timezone
import openpyxl
import tempfile
import shutil
from urllib.parse import quote
import time
import shutil
import getpass
import subprocess
import pytz


def encode_url_component(component):
    return quote(component, safe='')

def read_input_from_excel(input_file, row):
    wb = openpyxl.load_workbook(input_file)
    ws = wb.active
    server_url = ws.cell(row=row, column=1).value.strip() if ws.cell(row=row, column=1).value else ''
    collection_name = ws.cell(row=row, column=2).value.strip() if ws.cell(row=row, column=2).value else ''
    wiki_path = ws.cell(row=row, column=3).value.strip() if ws.cell(row=row, column=3).value else ''
    project_name = ws.cell(row=row, column=4).value.strip() if ws.cell(row=row, column=4).value else ''
    pat_token = ws.cell(row=row, column=5).value.strip() if ws.cell(row=row, column=5).value else ''
    return server_url, collection_name, project_name, wiki_path, pat_token

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

# def discover_wiki_pages(wiki_repo_path):
#     markdown_files = []
#     for root, _, files in os.walk(wiki_repo_path):
#         for file in files:
#             if file.endswith(".md"):  
#                 relative_path = os.path.relpath(os.path.join(root, file), wiki_repo_path)
#                 file_size = os.path.getsize(os.path.join(root, file))
#                 last_modified = datetime.fromtimestamp(os.path.getmtime(os.path.join(root, file)), timezone.utc)                
#                 last_modified = last_modified.replace(tzinfo=None)
#                 markdown_files.append((relative_path, file_size, last_modified))
#     return markdown_files

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
         



def write_report_to_excel(markdown_files, report_filename):
    # Check if the file is open and if it exists, delete it
    if os.path.exists(report_filename):
        try:
            os.remove(report_filename)  # Remove the file if it exists
        except PermissionError as e:
            print(f"Permission error when trying to delete {report_filename}: {e}")
            return
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Wiki Discovery Report"
    
    ws.append(["File Path", "Size (bytes)", "Last Modified"])

    for file in markdown_files:
        file_path, size, modified = file
        ws.append([file_path, size, modified])

    wb.save(report_filename)
    print(f"Discovery report saved as {report_filename}")

def handle_remove_readonly(func, path, excinfo):
    try:
        os.chmod(path, 0o777)  # Change the file mode to make it writable
        func(path)  # Retry the removal of the file
    except Exception as e:
        print(f"Error removing {path}: {e}")

def main():
    input_file = "wiki_discovery_input.xlsx"
    
    username = input("Enter your username: ").strip()  
    password = input("Enter your Password: ").strip()  
    encoded_password = encode_url_component(password)
    
    # Load the input Excel file
    wb = openpyxl.load_workbook(input_file)
    ws = wb.active
    
    for row in range(2, ws.max_row + 1):
        # Read data from the Excel file
        server_url = ws.cell(row=row, column=1).value.strip() if ws.cell(row=row, column=1).value else ''
        project_name = ws.cell(row=row, column=2).value.strip() if ws.cell(row=row, column=2).value else ''
        wiki_path = f"{project_name}.wiki"
        
        if not server_url or not project_name or not wiki_path:
            print(f"Skipping row {row}: missing necessary data.")
            continue
        
        # Extract collection from the server URL
        collection_name = server_url.split("/DefaultCollection")[0].strip()
        
        # Construct the URL for cloning
        clone_url = f"{server_url}/{project_name}/_git/{wiki_path}"
        auth_clone_url = clone_url.replace("://", f"://{username}:{encoded_password}@")
        
        # Cloning and processing the wiki
        temp_dir = clone_wiki_repo(auth_clone_url)
        if temp_dir:
            wiki_pages = discover_wiki_pages(temp_dir)
            if wiki_pages:
                report_filename = f"wiki_discovery_{project_name}.xlsx"
                write_report_to_excel(wiki_pages, report_filename)
            else:
                print(f"No wiki pages found for project: {project_name}.")
            
            time.sleep(1)
            shutil.rmtree(temp_dir, onexc=handle_remove_readonly)
            print(f"Temporary directory {temp_dir} cleaned up.")
        else:
            print(f"Failed to clone the repository for project {project_name}. Exiting.")
    
    print("Processing complete.")

if __name__ == "__main__":
    main()
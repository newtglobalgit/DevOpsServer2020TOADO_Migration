import ast
import json
import shutil
import requests
from requests.auth import HTTPBasicAuth
import openpyxl
import os
import subprocess
import pandas as pd

def fetch_discovered_pipelines():
    file_path ='tmp/discovery_pipeline.xlsx'
    df = pd.read_excel(file_path)

    for index, row in df.iterrows():
        name = row['FileName']

        if name != 'No path found':
            pipeline_id_discovery=row['Pipeline ID']
            pipline_name=row['Name']
            yaml_file_name = row['FileName']
            yaml_content, file_path,pipeline_name, yaml_file_name =fetch_pipeline_yaml(pipeline_id_discovery , pipline_name , yaml_file_name)
            # Fetch YAML from the source pipeline
            # yaml_content, file_path,pipeline_name, yaml_file_name = fetch_pipeline_yaml('' , '', '', )
            if not yaml_content:
                print("Failed to fetch YAML from the source pipeline.")
                return
            
            # Example usage
            excel_path = "target_credentials.xlsx"  # Path to target credentials Excel
            # yaml_file_path = "pipeline_4.yml"  # Path to YAML file

            # Step 1: Clone repo and push YAML file
            clone_and_push_yml_with_pat(excel_path, yaml_file_name)
            print("Current Directory:", os.getcwd())

            os.chdir("..")

            print("Current Directory:", os.getcwd())

            # Step 2: Fetch repository ID
            repo_id = get_repo_id_from_target(excel_path)
            # repo_id="9b2c8d2b-c271-400d-a006-e0c2c3855fb1"

            # Step 3: Create pipeline in the target repo
            if repo_id:
                create_pipeline_in_target(excel_path, yaml_file_name, repo_id,pipeline_name, row['Variables'])


def fetch_source_details(source_excel_path):
    
    # Load source credentials from Excel
    wb = openpyxl.load_workbook(source_excel_path)
    sheet = wb.active

    return sheet 
# Fetch Pipeline YAML from the source
def fetch_pipeline_yaml(pipeline_id_discovery , pipline_name ,yaml_file_name ):
    # sheet = fetch_source_details()
    instance , project , username , pat = sheet['A2'].value  , sheet['B2'].value, sheet['D2'].value, sheet['E2'].value   
    
    pipeline_id =pipeline_id_discovery

    # Endpoint to fetch pipeline details
    pipeline_details_url = f"{instance}/{project}/_apis/pipelines/{pipeline_id}?revision=1"

    # Fetch pipeline details
    pipeline_response = requests.get(
        pipeline_details_url,
        auth=HTTPBasicAuth(username, pat)
    )

    if pipeline_response.status_code != 200:
        print(f"Error fetching pipeline details: {pipeline_response.status_code} - {pipeline_response.text}")
        return

    pipeline_data = pipeline_response.json()
    print(pipeline_data)
    repo_id = pipeline_data["configuration"]["repository"]["id"]
    file_path = pipeline_data["configuration"]["path"]

    # Endpoint to download YAML file
    download_yaml_url = f"{instance}/{project}/_apis/git/repositories/{repo_id}/items?path={file_path}&api-version=6.0"

    yaml_response = requests.get(
        download_yaml_url,
        auth=HTTPBasicAuth(username, pat)
    )

    if yaml_response.status_code != 200:
        print(f"Error downloading YAML file: {yaml_response.status_code} - {yaml_response.text}")
        return

    # Save the YAML content to a file
    yaml_file_name = yaml_file_name
    with open(yaml_file_name, "w") as yaml_file:
        yaml_file.write(yaml_response.text)

    print(f"Pipeline YAML saved to {os.path.abspath(yaml_file_name)}")
    return yaml_response.text, file_path,pipline_name, yaml_file_name

def get_repo_id_from_target(excel_path):
    # Load details from Excel
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active

    base_url = sheet['A2'].value  # Base URL
    organization_project = sheet['B2'].value  # Organization and Project
    repo_name= sheet['C2'].value
    bearer_token = sheet['D2'].value  # Bearer Token

    # Endpoint to fetch repositories
    url = f"https://{base_url}/{organization_project}/_apis/git/repositories?api-version=4.1"

    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }

    response = requests.get(url, headers=headers, allow_redirects=True)

    if response.status_code != 200:
        print(f"Error fetching repositories: {response.status_code} - {response.text}")
        # return None

    # Parse the response
    repositories = response.json().get("value", [])
    if not repositories:
        print("No repositories found.")
        return None

    # Find the repository by name
    for repo in repositories:
        if repo.get("name") == repo_name:
            repo_id = repo.get("id")
            print(f"Repository ID for '{repo_name}': {repo_id}")
            return repo_id

    print(f"Repository with name '{repo_name}' not found.")
    return None


def create_pipeline_in_target(excel_path, yaml_file_name, repo_id,pipeline_name, variables):
    # Load details from Excel
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active

    base_url = sheet['A2'].value  # Base URL
    organization_project = sheet['B2'].value  # Organization and Project
    bearer_token = sheet['D2'].value  # Bearer Token

    # Endpoint to create a pipeline
    url = f"https://{base_url}/{organization_project}/_apis/pipelines?api-version=7.0"

    # Extract file name from the YAML file path
    # yaml_file_name = os.path.basename(yaml_file_path)

    # Payload for the POST request
    payload = {
        "name": pipeline_name,  # Unique name using last 4 characters of repo_id
        "folder": "\\",
        "configuration": {
            "type": "yaml",
            "path": f"/{yaml_file_name}",
            "repository": {
                "id": repo_id,
                "type": "azureReposGit",
                "refName": "refs/heads/main"
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data=response.json()
        target_pipeline_id = data.get('id')
        print(response.json())
        print("Pipeline successfully created!")

        variables_dict = ast.literal_eval(variables)
        # Check if the command was successful
        result = subprocess.run(
                    ["az.cmd", "login"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

        if result.returncode == 0:
            print("Login successful!")
            # Parse the JSON output
            base_url = f"https://{base_url}"
            account_info = json.loads(result.stdout)
            print(account_info)
            command = [
                "az.cmd", "devops", "configure",
                "--defaults",
                f"organization={base_url}",  # Combine key and value into a single string
                f"project={organization_project}"  # Combine key and value into a single string
            ]

            # Run the command
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Check the result
            if result.returncode == 0:
                print("Azure DevOps defaults configured successfully!")
                print(result.stdout)
                for var_name, properties in variables_dict.items():
                    if properties.get('isSecret') == None:
                    
                        command_var = [
                                "az.cmd", "pipelines", "variable", "create",
                                "--name", var_name,
                                "--pipeline-id", str(target_pipeline_id),
                                "--value", properties.get('value'),
                                "--project", organization_project  # Fixed syntax
                            ]
                        # Run the command
                        result = subprocess.run(
                            command_var,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )

                        # Check the result
                        if result.returncode == 0:
                            print(f"Pipeline variable '{var_name}' created successfully!")
                            print(result.stdout)
                        else:
                            print(f"Failed to create pipeline variable '{var_name}'.")
                            print(result.stderr)

            else:
                print("Failed to configure Azure DevOps defaults.")
                print(result.stderr)
        else:
            print("Login failed. Error:")
            print(result.stderr)
        
    else:
        print(f"Error creating pipeline: {response.status_code} - {response.text}")


def clone_and_push_yml_with_pat(excel_path, yaml_file_name):
    # Load details from Excel
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active

    base_url = sheet['A2'].value  # Base URL of the repository
    organization_project = sheet['B2'].value  # Organization and Project (e.g., 'jiraToAdo/Test1')
    repo_name = sheet['C2'].value  # Repository name (e.g., 'test1')
    pat_token = sheet['D2'].value  # Personal Access Token (PAT)
    # yaml_file_name = os.path.basename(yaml_file_path)  # Extract filename from path

    # Check if the repository already exists
    repo_url = f"https://{base_url}/{organization_project}/_apis/git/repositories/{repo_name}?api-version=6.0"
    headers = {
        "Authorization": f"Bearer {pat_token}",
        "Content-Type": "application/json",
    }

    response = requests.get(repo_url, headers=headers)

    if response.status_code == 200:
        print(f"Repository '{repo_name}' already exists.")
        # Extract repository clone URL
        repo_clone_url = response.json()["remoteUrl"]

        # Clone the repository locally
        os.system(f"git clone {repo_clone_url}")

    elif response.status_code == 404:
        print(f"Repository '{repo_name}' does not exist. Creating a new one.")

        # Construct API endpoint to create a repository
        create_repo_url = f"https://{base_url}/{organization_project}/_apis/git/repositories?api-version=6.0"
        payload = {
            "name": repo_name,
            "project": {"name": organization_project},
        }

        # Create the repository
        response = requests.post(create_repo_url, json=payload, headers=headers)

        if response.status_code == 201:
            print(f"Repository '{repo_name}' created successfully.")
            repo_clone_url = response.json()["remoteUrl"]

            # Clone the repository locally
            os.system(f"git clone {repo_clone_url}")
        else:
            print(f"Failed to create repository. Status Code: {response.status_code}")
            print("Response:", response.text)
            return
    else:
        print(f"Failed to check repository existence. Status Code: {response.status_code}")
        print("Response:", response.text)
        return

    # Add the .yml file to the repository
    repo_dir = repo_name  # Directory created by Git clone

    if os.path.exists(yaml_file_name):
        # Copy the .yml file to the repository directory
        shutil.copy(yaml_file_name, repo_dir)
        print(f"Successfully copied '{yaml_file_name}' to '{repo_dir}'.")

        # Change to the repository directory
        os.chdir(repo_dir)

        # Add, commit, and push the .yml file to the repository
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Add pipeline YAML file"], check=True)
        subprocess.run(["git", "push"], check=True)

        print(f"Added '{yaml_file_name}' to the repository and pushed changes.")

    else:
        print(f"YAML file '{yaml_file_name}' not found in the specified path.")

    
# Main execution function
if __name__ == "__main__":
    source_excel_path = "source_credentials.xlsx"  # Path to the source Excel file
    target_excel_path = "target_credentials.xlsx"  # Path to the target Excel file 
    sheet = fetch_source_details(source_excel_path)
    fetch_discovered_pipelines()
   
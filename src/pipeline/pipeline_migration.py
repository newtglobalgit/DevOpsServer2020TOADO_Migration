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
    file_path =f'src\pipeline\mapping_migration.xlsx'
    df = pd.read_excel(file_path)
    for index, row in df.iterrows():
        project_ = row['Project']
        name = row['FileName']
        is_classic = row['Classic Pipeline']
        pipeline_id_discovery=row['Pipeline ID']
        pipeline_name=row['Name']
        yaml_file_name = row['FileName']
        source_repo_name = row["Repository Name"]
        os.chdir(root)
        if name != 'NA' and (is_classic == 'No (Build)' or is_classic == 'No (Release)' ):
            result =clone_and_push_yml_with_pat( pipeline_id_discovery, pipeline_name, yaml_file_name, project_, source_repo_name)
            print("Current Directory:", os.getcwd())
            if result == "Exist":
                cloned =source_repo_name
                repo_id = get_repo_id_from_target( source_repo_name,project_)
            else: 
                cloned=target_repo
                repo_id = get_repo_id_from_target(target_repo,project_ )
            if repo_id:
                create_pipeline_in_target( yaml_file_name, repo_id,pipeline_name, row['Variables'], project_, pipeline_id_discovery)
                os.chdir(root)
        if is_classic == 'Yes':
            url = f"{source_instance}/{project_}/_apis/build/definitions/{pipeline_id_discovery}?api-version=6.1-preview"
            print(url)
            auth = HTTPBasicAuth('', source_pat)
            response = requests.get(url, auth=auth)
            def_file_name = f"src\pipeline\pipeline_definition.json"
            if response.status_code == 200:
                with open(def_file_name, 'w') as f:
                    json.dump(response.json(), f, indent=4)
                print("Pipeline definition has been saved to 'pipeline_definition.json'")

                # Load the original release definition JSON file
                with open(def_file_name, 'r') as f:
                    pipeline_data = json.load(f)

                populate_template(pipeline_data, template, project_)
                temp_file_name=f"src\pipeline\pipeline_template.json"
                # Write the populated template to a new JSON file
                with open(temp_file_name, 'w') as outfile:
                    json.dump(template, outfile, indent=4)

                print("The template has been populated and saved to 'pipeline_template.json'.")

                # Load the release payload from template.json
                with open(temp_file_name) as f:
                    pipeline_payload = json.load(f)

                url=f"{target_instance}/{project_}/_apis/build/definitions?api-version=7.2-preview.7"
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {target_pat}'
                }
                
                response = requests.post(url, headers=headers, data=json.dumps(pipeline_payload))
                
                if response.status_code == 200:
                    release = response.json()
                    print(f"Classic Pipeline created successfully! pipeline ID: {release['id']}")
                    print(f"Classic Pipeline URL: {release['_links']['self']['href']}")
                else:
                    print(f"Failed to create release. Status code: {response.status_code}")
                    print(response.text)
   
            else:
                print(f"Failed to fetch pipeline definition. Status code: {response.status_code}")
                print(response.text)

# Fetch Pipeline YAML from the source
def fetch_pipeline_yaml(pipeline_id_discovery , pipline_name ,yaml_file_name, project ):
    pipeline_id =pipeline_id_discovery
    pipeline_details_url = f"{source_instance}/{project}/_apis/pipelines/{pipeline_id}?revision=1"
    pipeline_response = requests.get(
        pipeline_details_url,
        auth=HTTPBasicAuth(source_username, source_pat)
    )
    if pipeline_response.status_code != 200:
        print(f"Error fetching pipeline details: {pipeline_response.status_code} - {pipeline_response.text}")
        return
    pipeline_data = pipeline_response.json()
    print(pipeline_data)
    repo_id = pipeline_data["configuration"]["repository"]["id"]
    file_path = pipeline_data["configuration"]["path"]
    # Endpoint to download YAML file
    download_yaml_url = f"{source_instance}/{project}/_apis/git/repositories/{repo_id}/items?path={file_path}&api-version=6.0"
    yaml_response = requests.get(
        download_yaml_url,
        auth=HTTPBasicAuth(source_username, source_pat)
    )
    if yaml_response.status_code != 200:
        print(f"Error downloading YAML file: {yaml_response.status_code} - {yaml_response.text}")
        return
    # Save the YAML content to a file
    yaml_file_name = f"{root}\src\pipeline\{yaml_file_name}"
    with open(yaml_file_name, "w") as yaml_file:
        yaml_file.write(yaml_response.text)
    print(f"Pipeline YAML saved to {os.path.abspath(yaml_file_name)}")
    return yaml_response.text, file_path,pipline_name, yaml_file_name

def get_repo_id_from_target(repo_,organization_project):
    if repo_ == '':
        repo_= target_repo
    # Endpoint to fetch repositories
    url = f"{target_instance}/{organization_project}/_apis/git/repositories?api-version=4.1"
    headers = {
        "Authorization": f"Bearer {target_pat}"
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
        if repo.get("name") == repo_:
            repo_id = repo.get("id")
            print(f"Repository ID for '{repo_}': {repo_id}")
            return repo_id
    print(f"Repository with name '{repo_}' not found.")
    return None


def create_pipeline_in_target( yaml_file_name, repo_id,pipeline_name, variables, organization_project,pipeline_id):
    # Endpoint to create a pipeline
    url = f"{target_instance}/{organization_project}/_apis/pipelines?api-version=7.0"
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
        "Authorization": f"Bearer {target_pat}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data=response.json()
        target_pipeline_id = data.get('id')
        print(response.json())
        print("Pipeline successfully created!")
        file_url = f"{source_instance}/{organization_project}/_apis/pipelines/{pipeline_id}?revision=1"
        response = requests.get(file_url, auth=HTTPBasicAuth(source_username, source_pat))
        data = response.json()
        variable_groups ={}
        variables={}
        detailedJson = data['configuration'].get('designerJson')
        agent_details = ""
        artifact_details=""
        phases_=[]
        if detailedJson:
            variables = data['configuration']['designerJson'].get('variables', "")
            variable_groups = data['configuration']['designerJson'].get('variableGroups',"")
        else:
            variables = data['configuration'].get('variables', "")
            variable_groups = data['configuration'].get('variableGroups',"")
        if variables !='':
            variables_dict = variables
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
                base_url = f"{target_instance}"
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
            print("Varibale not Exist for this pipeline")  
    else:
        print(f"Error creating pipeline: {response.status_code} - {response.text}")

def clone_and_push_yml_with_pat( pipeline_id , pipeline_name ,yaml_file_name, organization_project,source_repo_name): 
    # Check if the repository already exists
    repo_url = f"{target_instance}/{organization_project}/_apis/git/repositories/{source_repo_name}?api-version=6.0"
    headers = {
        "Authorization": f"Bearer {target_pat}",
        "Content-Type": "application/json",
    }
    response = requests.get(repo_url, auth=HTTPBasicAuth("",target_pat))
    if response.status_code == 200:
        print(f"Repository '{source_repo_name}' already exists.")
        # Extract repository clone URL
        repo_clone_url = response.json()["remoteUrl"]
        current =os.getcwd()
        if current != f"{root}\src\pipeline":
            os.chdir(f"{current}\src\pipeline")
            current_ = os.getcwd()
        # Clone the repository locally
        os.system(f"git clone {repo_clone_url}")
        os.chdir(f"{current_}\{source_repo_name}")
    elif response.status_code == 404:
        print(f"Repository '{target_repo}' does not exist. Creating a new one.")
        # Construct API endpoint to create a repository
        create_repo_url = f"{target_instance}/{organization_project}/_apis/git/repositories?api-version=6.0"
        payload = {
            "name": target_repo,
            "project": {"name": organization_project},
        }
        # Create the repository
        response = requests.post(create_repo_url, json=payload, headers=headers)
        if response.status_code == 201:
            print(f"Repository '{target_repo}' created successfully.")
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
    print(os.getcwd())
    if os.path.exists(yaml_file_name):
        print("Yaml file exist")
        return "Exist"
    else:
        os.chdir("..")
        print(f"YAML file '{yaml_file_name}' not found in the specified path.")
        source_repo_name = target_repo
        repo_dir = target_repo
        repo_url = f"{target_instance}/{organization_project}/_apis/git/repositories/{source_repo_name}?api-version=6.0"
        headers = {
            "Authorization": f"Bearer {target_pat}",
            "Content-Type": "application/json",
        }
        response = requests.get(repo_url, auth=HTTPBasicAuth("",target_pat))
        if response.status_code == 200:
            print(f"Repository '{source_repo_name}' already exists.")
            repo_clone_url = response.json()["remoteUrl"]
            current =os.getcwd()
            if current != f"{root}\src\pipeline":
                os.chdir(f"{current}\src\pipeline")
            os.system(f"git clone {repo_clone_url}")
        yaml_content, file_path,pipeline_name, yaml_file_name =fetch_pipeline_yaml(pipeline_id , pipeline_name , yaml_file_name, organization_project)
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
        return "Not Exist"
    



# Function to load data into template
def populate_template(pipeline_data, template, project_):
    # Populate template with data from the release JSON

    # Populating the "options" section
    template["options"] = pipeline_data.get("options", [])

    # Populating the "variables" section
    template["variables"] = pipeline_data.get("variables", {})

    # Populating the "variableGroups" section
    template["variableGroups"] = pipeline_data.get("variableGroups", [])
    variableGroups = pipeline_data.get("variableGroups", [])
    for variableGroup in variableGroups:
        variable_group_name = variableGroup['name']
        variable_group_id = check_variable_group_exists_by_name(variable_group_name,project_)
        print(variable_group_id)
        if variable_group_id:
            variableGroup['id']= variable_group_id
        else:
            create_variable_groups(variableGroup, project_)
    # Populating the "_links" section
    template["_links"] = pipeline_data.get("_links", {})

    # Populating "buildNumberFormat"
    template["buildNumberFormat"] = pipeline_data.get("buildNumberFormat", "")

    # Populating "comment"
    template["comment"] = pipeline_data.get("comment", "")

    # Populating "jobAuthorizationScope"
    template["jobAuthorizationScope"] = pipeline_data.get("jobAuthorizationScope", "")

    # Populating "jobTimeoutInMinutes"
    template["jobTimeoutInMinutes"] = pipeline_data.get("jobTimeoutInMinutes", 0)

    # Populating "jobCancelTimeoutInMinutes"
    template["jobCancelTimeoutInMinutes"] = pipeline_data.get("jobCancelTimeoutInMinutes", 0)

    # Populating the "process" section
    template["process"] = pipeline_data.get("process", {})

    phases =pipeline_data['process'].get("phases", {})
    for phase in phases:
        queue =phase['target'].get('queue',{})
        if queue != {}:
            queue_id = queue['id']
            queue_url=queue['url']
            target_queue_id =get_agent_pool_details("",queue_id, queue_url, project_)
            queue['id']=target_queue_id

    # Populating the "repository" section
    template["repository"] = pipeline_data.get("repository", {})
    repository = pipeline_data.get("repository", {})
    repository_name = repository.get('name',"")
    repository_type = repository.get('name',"")

    print(repository_name)
    print(repository_type)
    repo_id=""
    if repository_type != 'TfsVersionControl' :

        # API endpoint
        url = f'{target_instance}/{project_}/_apis/git/repositories?api-version=7.1-preview.1'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {target_pat}'
        }
        # Send GET request
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            repositories = response.json()['value']

            # Find the repository with the desired name
            for repo in repositories:
                if repo['name'] == repository_name:
                    repo_id = repo['id']
                    print(f"Repository ID for {repository_name}: {repo_id}")
        else:
            print(f"Failed to fetch repositories. Status Code: {response.status_code}- {response.text}")
    else:
        url= f""
    # repository.set(id,repo_id)
    repository['id'] = repo_id
    print(repository)
    # Populating "processParameters"
    template["processParameters"] = pipeline_data.get("processParameters", {})

    # Populating "quality"
    template["quality"] = pipeline_data.get("quality", "")

    # Populating "authoredBy" section
    template["authoredBy"] = pipeline_data.get("authoredBy", {})

    # Populating "drafts" section
    template["drafts"] = pipeline_data.get("drafts", [])

    # Populating the "queue" section
    template["queue"] = pipeline_data.get("queue", {})
    queue =pipeline_data.get("queue", {})
    queue_id = queue['id'] 
    queue_name = queue['name']
    agent_pool_details = get_agent_pool_details(queue_name,"","",project_)
    queue['id']=agent_pool_details

    # Populating the "id", "name", "url", "uri", "path" etc.
    template["id"] = pipeline_data.get("id", 0)
    template["name"] = pipeline_data.get("name", "")
    template["url"] = pipeline_data.get("url", "")
    template["uri"] = pipeline_data.get("uri", "")
    template["path"] = pipeline_data.get("path", "")
    template["type"] = pipeline_data.get("type", "")
    template["queueStatus"] = pipeline_data.get("queueStatus", "")
    template["revision"] = pipeline_data.get("revision", 0)
    template["createdDate"] = pipeline_data.get("createdDate", "")
    
    # Populating the "project" section
    template["project"] = pipeline_data.get("project", {})
    project_data = pipeline_data.get("project",{})
    if project_data:
        
        proj_name= project_data.get("name", "")
        project_id , collection_id =get_proj_details(proj_name)
        project_id_source = template["project"]["id"]
        template["project"]["id"] = project_id
        replace_project_id(template, project_id_source, project_id, project_)

def create_variable_groups(variable_group, project_):
    print(variable_group)
    url = f"{target_instance}/{project_}/_apis/distributedtask/variablegroups?api-version=6.0"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {target_pat}'
    }
    variable_group_data = variable_group.copy()
    proj_id , collection_id = get_proj_details(project_)

    variable_group_data['variableGroupProjectReferences'] = [{
    "name": variable_group['name'],
    "projectReference": {
        "id": proj_id,
        "name": project_
    }    }
    ]
    print(variable_group_data)
    response = requests.post(url , headers=headers, data=json.dumps(variable_group_data))
    if response.status_code==200:
        data = response.json()
        print(data)
    else:
        print(response.text)

def get_agent_pool_details(queue_name, queue_id, queue_url,project_):
    if queue_name!='':
        url=f"{target_instance}/{project_}/_apis/distributedtask/queues?api-version=6.0-preview"
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {target_pat}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            queues = data['value']
            for queue in queues:
                if queue['name']==queue_name:
                    return queue['id']
        else:
            return False
    if queue_id !='':
        source_organization_url =queue_url.split('/_api')[0]
        url = f"{source_organization_url}/{project_}/_apis/distributedtask/queues/{queue_id}?api-version=6.0-preview"
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {source_pat}'
        }
        response = requests.get(url,  auth=HTTPBasicAuth("lexcon", source_pat))
        if response.status_code == 200:
            data = response.json()
            queue_name = data['name']
            queue_id =get_agent_pool_details(queue_name, "","", project_)
            return queue_id
        else:
            print("Error in fetch agent details in source")
            return False

    
    
def check_variable_group_exists_by_name(variable_group_name,project_):
    url = f"{target_instance}/{project_}/_apis/distributedtask/variablegroups?api-version=6.0"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {target_pat}'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        for group in data.get('value', []):
            if group['name'] == variable_group_name:
                print(f"Variable group '{variable_group_name}' found!")
                return group['id']  # Return the ID of the existing variable group
        print(f"Variable group '{variable_group_name}' not found.")
        return None
    else:
        print(f"Failed to fetch variable groups. Status Code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

def replace_project_id(data, old_id, new_id, project_):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and old_id in value:
                data[key] = value.replace(old_id, new_id)
            else:
                replace_project_id(value, old_id, new_id, project_)
    elif isinstance(data, list):
        for item in data:
            replace_project_id(item, old_id, new_id, project_)

def get_def_details(def_name, project_):
    url = f"{target_instance}{project_}/_apis/build/definitions?api-version=6.0"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {target_pat}'
    }
    response = requests.get(url, headers=headers)
    # print(url)    
    if response.status_code == 200:
        build_definitions = response.json().get('value', [])
        # print(build_definitions)
        for definition in build_definitions:
            if definition['name'].lower() == def_name.lower():
                def_id = definition['id']
                print(f"Build Definition ID for '{def_name}': {def_id}")
                return def_id
        print(f"Build definition '{def_name}' not found.")
        return None
    else:
        print(f"Failed to retrieve build definitions. Status code: {response.status_code}")
        return None
    
def get_proj_details(proj_name):
    url = f"{target_instance}/_apis/projects/{proj_name}?api-version=7.1-preview.1"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {target_pat}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        proj_details = response.json()
        proj_id = response.json().get('id', "")
        collection_url = proj_details.get('collection').get('url') 
        temp = collection_url.split('/')
        collection_id = temp[6]
       
        return proj_id , collection_id
    else:
        print(f"Failed to retrieve build definitions. Status code: {response.status_code}")
        return None
    
# Main execution function
if __name__ == "__main__":
    source_excel_path = "credentials.xlsx"  # Path to the source Excel file
    root = os.getcwd()
    template = {
        "options": [],
        "variables": {},
        "variableGroups": [],
        "properties": {},
        "tags": [],
        "_links": {},
        "buildNumberFormat": "",
        "comment": "",
        "jobAuthorizationScope": "",
        "jobTimeoutInMinutes": 0,
        "jobCancelTimeoutInMinutes": 0,
        "process": {
            "phases": [],
            "type": 1
        },
        "repository": {},
        "processParameters": {
            "inputs": []
        },
        "quality": "",
        "authoredBy": {},
        "drafts": [],
        "queue": {},
        "id": 0,
        "name": "",
        "url": "",
        "uri": "",
        "path": "",
        "type": "build",
        "queueStatus": "enabled",
        "revision": 0,
        "createdDate": "",
        "project": {}
    }
    # Read the Excel file
    credentials = pd.read_excel(f'src\pipeline\credentials.xlsx')
    # Iterate over each row in the DataFrame
    for index, row in credentials.iterrows():
        source_instance = row["Source_URL"]	
        source_username = row["Source_Username"]
        source_pat = row["Source_Pat"]
        target_instance =row["Target_URL"]
        target_username =row["Target_Username"]
        target_pat=row["Target_Pat"]
        target_repo = row["repo"]  
    fetch_discovered_pipelines()
    
   
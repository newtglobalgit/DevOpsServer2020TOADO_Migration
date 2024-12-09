import json
from requests.auth import HTTPBasicAuth
import requests

# Load the original release definition JSON file
with open('pipeline_definition.json', 'r') as f:
    pipeline_data = json.load(f)


# Function to load data into template
def populate_template(pipeline_data, template):
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
        variable_group_id = check_variable_group_exists_by_name(variable_group_name)
        print(variable_group_id)
        if variable_group_id:
            variableGroup['id']= variable_group_id
        else:
            create_variable_groups(variableGroup)
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
            target_queue_id =get_agent_pool_details("",queue_id, queue_url)
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
        url = f'{organization_url}/{project_name}/_apis/git/repositories?api-version=7.1-preview.1'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {pat_token}'
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
    agent_pool_details = get_agent_pool_details(queue_name,"","")
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
        replace_project_id(template, project_id_source, project_id)

def create_variable_groups(variable_group):
    print(variable_group)
    url = f"{organization_url}/{project_name}/_apis/distributedtask/variablegroups?api-version=6.0"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {pat_token}'
    }
    variable_group_data = variable_group.copy()
    proj_id , collection_id = get_proj_details(project_name)

    variable_group_data['variableGroupProjectReferences'] = [{
    "name": variable_group['name'],
    "projectReference": {
        "id": proj_id,
        "name": project_name
    }    }
    ]

 
        
    
    print(variable_group_data)
    response = requests.post(url , headers=headers, data=json.dumps(variable_group_data))
    if response.status_code==200:
        data = response.json()
        print(data)
    else:
        print(response.text)



import requests
import json

# def create_variable_group( ):
#     # Define the URL for the API request
#     url = f'{organization_url}/{project_name}/_apis/distributedtask/variablegroups?api-version=7.1'
#     proj_id , collect_id = get_proj_details(project_name)
#     # Prepare the request body
#     variable_group_data =  {
#     "variables": {
#         "ConnectionString": {
#         "value": "YourConnectionString",
#         "isSecret": True
#         },
#         "APIKey": {
#         "value": "YourAPIKey",
#         "isSecret": True
#         },
#         "Environment": {
#         "value": "Production"
#         }
#     },
#     "variableGroupProjectReferences": [
#         {
#         "name": "NewVariableGroup",
#         "projectReference": {
#             "id": proj_id,
#             "name": project_name
#         }
#         }
#     ],
#     "name": "NewVariableGroup",
#     "description": "Description of your variable group"
#     }

    # # Set the headers for the request
    # headers = {
    #     'Content-Type': 'application/json',
    #     'Authorization': f'Bearer {pat_token}'
    # }

    # # Send the POST request to create the variable group
    # response = requests.post(url, headers=headers, data=json.dumps(variable_group_data))

    # # Check the response status
    # if response.status_code == 200:
    #     print("Variable group created successfully")
    #     print(response.json())
    # else:
    #     print(f"Failed to create variable group. Status Code: {response.status_code}")
    #     print(f"Error Message: {response.text}")


# Create the variable group





def get_agent_pool_details(queue_name, queue_id, queue_url):
    if queue_name!='':
        url=f"{organization_url}/{project_name}/_apis/distributedtask/queues?api-version=6.0-preview"
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {pat_token}'
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
        url = f"{source_organization_url}/{project_name}/_apis/distributedtask/queues/{queue_id}?api-version=6.0-preview"
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {source_pat}'
        }
        response = requests.get(url,  auth=HTTPBasicAuth("lexcon", source_pat))
        if response.status_code == 200:
            data = response.json()
            queue_name = data['name']
            queue_id =get_agent_pool_details(queue_name, "","")
            return queue_id
        else:
            print("Error in fetch agent details in source")
            return False

    
    
def check_variable_group_exists_by_name(variable_group_name):
    url = f"{organization_url}/{project_name}/_apis/distributedtask/variablegroups?api-version=6.0"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {pat_token}'
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

def replace_project_id(data, old_id, new_id):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and old_id in value:
                data[key] = value.replace(old_id, new_id)
            else:
                replace_project_id(value, old_id, new_id)
    elif isinstance(data, list):
        for item in data:
            replace_project_id(item, old_id, new_id)

def get_def_details(def_name):
    url = f"{organization_url}{project_name}/_apis/build/definitions?api-version=6.0"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {pat_token}'
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
    url = f"{organization_url}/_apis/projects/{proj_name}?api-version=7.1-preview.1"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {pat_token}'
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
    
if __name__ == "__main__":
    organization_url = "https://dev.azure.com/PLMigration"
    organization_name = "PLMigration"
    project_name = "CatCore"
    pat_token = ""
    source_pat = ""
    # Define the empty template structure
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

    # Populate the template with the data from the release_definition.json
    populate_template(pipeline_data, template)

    # Output the populated template
    print(json.dumps(template, indent=4))

    # Write the populated template to a new JSON file
    with open('pipeline_template.json', 'w') as outfile:
        json.dump(template, outfile, indent=4)

    print("The template has been populated and saved to 'pipeline_template.json'.")

    # Load the release payload from template.json
    with open('pipeline_template.json') as f:
        pipeline_payload = json.load(f)

    url=f"{organization_url}/{project_name}/_apis/build/definitions?api-version=7.2-preview.7"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {pat_token}'
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(pipeline_payload))
    
    if response.status_code == 200:
        release = response.json()
        print(f"Classic Pipeline created successfully! pipeline ID: {release['id']}")
        print(f"Classic Pipeline URL: {release['_links']['self']['href']}")
    else:
        print(f"Failed to create release. Status code: {response.status_code}")
        print(response.text)
   
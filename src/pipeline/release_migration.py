import json
import os
import re
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth


# Function to load data into template
def populate_template(release_data, template):
    # Populate template with data from the release JSON
    template["source"] = release_data.get("source", "")
    template["revision"] = release_data.get("revision", 0)
    template["description"] = release_data.get("description", "")
    template["createdBy"] = {
        "displayName": release_data["createdBy"].get("displayName", ""),
        "id": release_data["createdBy"].get("id", ""),
        "uniqueName": release_data["createdBy"].get("uniqueName", "")
    }
    template["createdOn"] = release_data.get("createdOn", "")
    # template["modifiedBy"] = release_data.get("modifiedBy", {})
    template["modifiedOn"] = release_data.get("modifiedOn", "")
    template["isDeleted"] = release_data.get("isDeleted", False)
    
    if "lastRelease" in release_data:
        template["lastRelease"] = {
            "id": release_data["lastRelease"].get("id", 0),
            "name": release_data["lastRelease"].get("name", ""),
            # "artifacts": release_data["lastRelease"].get("artifacts", []),
            "_links": release_data["lastRelease"].get("_links", {}),
            "description": release_data["lastRelease"].get("description", ""),
            "releaseDefinition": {
                "id": release_data["lastRelease"]["releaseDefinition"].get("id", 0),
                "projectReference": release_data["lastRelease"]["releaseDefinition"].get("projectReference", None),
                "_links": release_data["lastRelease"]["releaseDefinition"].get("_links", {})
            },
            "createdOn": release_data["lastRelease"].get("createdOn", ""),
            "createdBy": release_data["lastRelease"]["createdBy"],
        }

    template["variables"] = release_data.get("variables", {})
    template["variableGroups"] = release_data.get("variableGroups", [])
    target_variableGroups =[]
    variableGroups = list(template["variableGroups"])
    for variableGroup in variableGroups:
        v_group, variableGroup_name = check_variable_group_exists_by_id(variableGroup)
        print(variableGroup_name)
        if variableGroup_name:
            variableGroup_id =check_variable_group_exists_by_name(variableGroup_name)
            if variableGroup_id: 
                target_variableGroups.append(variableGroup_id)
            else:
                id = create_variable_groups(v_group)
                target_variableGroups.append(id)
    template["variableGroups"] = target_variableGroups
    print(target_variableGroups)
    
    j=0
    template["environments"] = release_data.get("environments", [])
    environments  = release_data.get("environments",[])
    if environments:
        for environment in environments:
            i =0
            target_variableGroups_=[]
            deployPhases = environment["deployPhases"]
            variableGroups_ = release_data['environments'][j].get('variableGroups',[])
            for variableGroup_ in variableGroups_:
                v_group_, variableGroup_name_ = check_variable_group_exists_by_id(variableGroup_)
                print(variableGroup_name_)
                if variableGroup_name_:
                    variableGroup_id_ =check_variable_group_exists_by_name(variableGroup_name_)
                    if variableGroup_id_: 
                        target_variableGroups_.append(variableGroup_id_)
                    else:
                        id_ = create_variable_groups(v_group_)
                        target_variableGroups_.append(id_)
            release_data['environments'][j]['variableGroups'] = target_variableGroups_
            for deployPhase in deployPhases:
                deploymentInput = deployPhase.get("deploymentInput","")
                queue_id = deploymentInput.get("queueId","")
                if queue_id:
                    target_queue_id =get_agent_pool_details("",queue_id)
                    release_data['environments'][j]['deployPhases'][i]['deploymentInput']["queueId"] = target_queue_id
                i=i+1
            j=j+1
    template["environments"]= release_data["environments"]
    # template["artifacts"] = []
    # for artifact in release_data.get("artifacts", []):
            
    #     definition= artifact.get("definitionReference", {}).get("definition", {})
    #     def_name = definition.get('name')
    #     def_id = get_def_details(def_name)

    #     if def_id:
    #         artifact["definitionReference"]["definition"]["id"] = def_id
    #         # print(f"Updated artifact definition ID: {def_id}")
    #     else:
    #         print(f"Build definition '{def_name}' not found. Artifact definition ID not updated.")

    #     # print("Print the updated artifact (just for confirmation)")
    #     # print(artifact)
    #     project =  artifact.get("definitionReference", {}).get("project", {})
    #     proj_name = project.get('name')
    #     proj_id , collection_id  = get_proj_details(proj_name)
    #     if proj_id:
    #         artifact["definitionReference"]["project"]["id"] = proj_id
    #         # print(f"Updated artifact definition ID: {def_id}")
    #     else:
    #         print(f"Proj Id '{proj_name}' not found. Artifact definition ID not updated.")
    #     repository = artifact.get("definitionReference", {}).get("repository", {})
    #     artifactSourceDefinitionUrl = artifact.get("definitionReference").get("artifactSourceDefinitionUrl", {})
    #     artifactSourceDefinitionUrl_id= str(artifactSourceDefinitionUrl.get("id", ""))
       
    #     if collection_id and proj_id:
    #         # artifactSourceDefinitionUrl_id= artifactSourceDefinitionUrl_id.replace(
    #         #     'collectionId=10b92735-bebc-4b8e-9cf5-582ba85c5915', f'collectionId={collection_id}'
    #         # ).replace(
    #         #     'projectId=76f16046-3d64-411d-9552-115a665388d9', f'projectId={proj_id}'
    #         # )
    #         artifactSourceDefinitionUrl_id = re.sub(
    #             r'collectionId=[^&]+',  # Match collectionId and its value
    #             f'collectionId={collection_id}',  # Replace with new collectionId
    #             artifactSourceDefinitionUrl_id
    #         )

    #         artifactSourceDefinitionUrl_id = re.sub(
    #             r'projectId=[^&]+',  # Match projectId and its value
    #             f'projectId={proj_id}',  # Replace with new projectId
    #             artifactSourceDefinitionUrl_id
    #         )
    #         artifactSourceDefinitionUrl_id = re.sub(
    #             r'definitionId=[^&]+',  # Match projectId and its value
    #             f'definitionId={def_id}',  # Replace with new projectId
    #             artifactSourceDefinitionUrl_id
    #         )
    #         artifact["definitionReference"]["artifactSourceDefinitionUrl"]["id"] = artifactSourceDefinitionUrl_id
    #         artifactSourceDefinitionUrl["id"]=artifactSourceDefinitionUrl_id
    #         print(f"Updated artifactSourceDefinitionUrl: {artifactSourceDefinitionUrl_id}")
    #         # print(artifactSourceDefinitionUrl.get("id"))
    #     else:
    #         print("Collection ID or Project ID missing. artifactSourceDefinitionUrl not updated.")
    # for artifact in release_data.get("artifacts", []):
    #     elaborate_artifact = {
    #         "sourceId": artifact.get("sourceId", ""),
    #         "type": artifact.get("type", ""),
    #         "alias": artifact.get("alias", ""),
    #         "definitionReference": {
    #             "defaultVersionBranch": artifact.get("definitionReference", {}).get("defaultVersionBranch", {}),
    #             "defaultVersionSpecific": artifact.get("definitionReference", {}).get("defaultVersionSpecific", {}),
    #             "defaultVersionTags": artifact.get("definitionReference", {}).get("defaultVersionTags", {}),
    #             "defaultVersionType": artifact.get("definitionReference", {}).get("defaultVersionType", {}),
    #             "definition": definition,
    #             "definitions": artifact.get("definitionReference", {}).get("definitions", {}),
    #             "IsMultiDefinitionType": artifact.get("definitionReference", {}).get("IsMultiDefinitionType", ""),
    #             "project" : project,
    #             "repository" : repository, 
    #             "artifactSourceDefinitionUrl": artifactSourceDefinitionUrl

    #         },
    #         "isPrimary": artifact.get("isPrimary", False),
    #         "isRetained": artifact.get("isRetained", False),
    #         "_links": artifact.get("_links", {}),
    #     }
    #     template["artifacts"].append(elaborate_artifact)
    template["triggers"] = release_data.get("triggers", [])
    template["releaseNameFormat"] = release_data.get("releaseNameFormat", "")
    template["tags"] = release_data.get("tags", [])
    template["properties"] = release_data.get("properties", {})
    # template["id"] = release_data.get("id", 0)
    template["name"] = release_data.get("name", "")
    template["path"] = release_data.get("path", "")
    template["projectReference"] = release_data.get("projectReference", None)

def create_variable_groups(variable_group):
    print(variable_group)
    url = f"{organization_url}/{source_project_name}/_apis/distributedtask/variablegroups?api-version=6.0"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {pat_token}'
    }
    variable_group_data = variable_group.copy()
    proj_id , collection_id = get_proj_details(source_project_name)

    variable_group_data['variableGroupProjectReferences'] = [{
    "name": variable_group['name'],
    "projectReference": {
        "id": proj_id,
        "name": source_project_name
    }    }
    ]
    print(variable_group_data)
    response = requests.post(url , headers=headers, data=json.dumps(variable_group_data))
    if response.status_code==200:
        data = response.json()
        print(data)
        return data['id']
    else:
        print(response.text)
        return

def get_agent_pool_details(queue_name, queue_id):
    if queue_name!='':
        url=f"{organization_url}/{source_project_name}/_apis/distributedtask/queues?api-version=6.0-preview"
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
        url = f"{source_organization_url}/{source_project_name}/_apis/distributedtask/queues/{queue_id}?api-version=6.0-preview"
        response = requests.get(url,  auth=HTTPBasicAuth("lexcon", source_pat_token))
        if response.status_code == 200:
            data = response.json()
            queue_name = data['name']
            queue_id =get_agent_pool_details(queue_name, "")
            return queue_id
        else:
            print("Error in fetch agent details in source")
            return False

    
    
def get_def_details(def_name):
    url = f"{organization_url}{source_project_name}/_apis/build/definitions?api-version=6.0"
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
    
def check_variable_group_exists_by_name(variable_group_name):
    url = f"{organization_url}/{source_project_name}/_apis/distributedtask/variablegroups?api-version=6.0"
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

def check_variable_group_exists_by_id(variable_group_id):
    v_group={}
    url = f"{source_organization_url}/{source_project_name}/_apis/distributedtask/variablegroups?api-version=6.0-preview"
    response = requests.get(url, auth=HTTPBasicAuth("",source_pat_token))
    print(url)
    if response.status_code == 200:
        data = response.json()
        for group in data.get('value', []):
            if group['id'] == variable_group_id:
                variable_group_name = group['name']
                print(f"Variable group '{variable_group_name}' found!")
                return group,group['name']  # Return the ID of the existing variable group
        print(f"Variable group with '{variable_group_id}' not found in source.")
        return None
    else:
        print(f"Failed to fetch variable groups. Status Code: {response.status_code}")
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


def create_release(organization_name, project_name, pat_token, release_payload):
    # url = f"{organization_url}/{project_name}/_apis/release/releases?api-version=7.2-preview.4"
    url =f"https://vsrm.dev.azure.com/{organization_name}/{project_name}/_apis/release/definitions?api-version=7.2-preview.4"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {pat_token}'
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(release_payload))
    
    if response.status_code == 200:
        release = response.json()
        print(f"Release created successfully! Release ID: {release['id']}")
        print(f"Release URL: {release['_links']['self']['href']}")
    else:
        print(f"Failed to create release. Status code: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    folder_path = os.path.join("src","pipeline")
    credentials = pd.read_excel(f"{folder_path}\credentials.xlsx")
    for index ,row in credentials.iterrows():
        # organization_url = "https://dev.azure.com/PLMigration/"
        # organization_name = "PLMigration"
        # project_name = "CatCore"
        # pat_token = ""
        # source_organization_url = "http://172.191.4.85/DefaultCollection/"
        # source_organization_name = "DefaultCollection"
        # source_project_name = "CatCore"
        # source_pat_token = ""
        organization_url = str(row["Target_URL"])
        organization_name =organization_url.split("/")[-1]
        project_name = row["Target_Project"]
        pat_token = row["Target_Pat"]
        source_organization_url = str(row["Source_URL"])
        source_organization_name = source_organization_url.split("/")[-1]
        source_project_name =row["Source_Project"]
        source_pat_token = row["Source_Pat"]
    release_discovery = pd.read_excel(f"{folder_path}\output_folder\source_discovery_release.xlsx")
    for index, row in release_discovery.iterrows():
        definition_id = row["Release ID"]
        json_file = os.path.join(folder_path,"release_definition.json")
        source_project_name = row["Project"]
        url = f"{source_organization_url}/{source_project_name}/_apis/release/definitions/{definition_id}?api-version=6.1-preview"
        response = requests.get(url, auth=HTTPBasicAuth('', source_pat_token))

        # Check if the request was successful
        if response.status_code == 200:
            release_pipeline = response.json()
            with open(json_file, 'w') as file:
                json.dump(release_pipeline, file, indent=4)
            print(f"Pipeline definition successfully exported to {json_file}")
        else:
            print(f"Failed to fetch release pipeline. Status Code: {response.status_code}")
            print(response.text)        
        # Load the original release definition JSON file
        with open(json_file, 'r') as f:
            release_data = json.load(f)

        # Template structure
        template = {
            "source": "",
            "revision": 0,
            "description": "",
            "createdBy": {
                "displayName": "",
                "id": "",
                "uniqueName": ""
            },
            "createdOn": "",
            "modifiedBy": {},
            "modifiedOn": "",
            "isDeleted": False,
            "lastRelease": {
                "id": 0,
                "name": "",
                "artifacts": [],
                "_links": {},
                "description": "",
                "releaseDefinition": {
                    "id": 0,
                    "projectReference": None,
                    "_links": {}
                },
                "createdOn": "",
                "createdBy": {
                    "displayName": "",
                    "url": "",
                    "_links": {
                        "avatar": {
                            "href": ""
                        }
                    },
                    "id": "",
                    "uniqueName": "",
                    "imageUrl": "",
                    "descriptor": ""
                }
            },
            "variables": {},
            "variableGroups": [],
            "environments": [],
            "artifacts": [],
            "triggers": [],
            "releaseNameFormat": "",
            "tags": [],
            "properties": {},
            "name": "",
            "path": "",
            "projectReference": None
        }

        # Populate template with the data from the original JSON
        populate_template(release_data, template)
        with open(json_file, 'w') as f:
            json.dump(template, f, indent=4)

        print("Template JSON has been created and saved as template.json.")

        with open(json_file) as f:
            release_payload = json.load(f)

        create_release(organization_name, source_project_name, pat_token, release_payload)



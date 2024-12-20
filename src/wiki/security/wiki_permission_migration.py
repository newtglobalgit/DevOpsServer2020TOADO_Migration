import json
import requests
import pandas as pd
import urllib
import xlsxwriter
from requests.auth import HTTPBasicAuth


def migrate_permissions(payload):
    """Call the ManagePermissions API to apply the permissions."""
    try:
        url = f"{target_ado_server_url}/{target_project_name}/_api/_security/ManagePermissions?__v=5"
        payload1 = {"updatePackage": json.dumps(payload)}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload1, auth=HTTPBasicAuth("",target_pat))
        response.raise_for_status()
        return response.status_code
    except Exception as e:
        print(f"Failed to migrate permissions for target project '{target_project_name}': {e}")
        raise

def get_proj_details(ado_url, pat_token, proj_name):
    try:
        url = f"{target_ado_server_url}/_apis/projects/{proj_name}?api-version=6.1-preview"
        response = requests.get(url, auth=HTTPBasicAuth("", pat_token))
        if response.status_code == 200:
            proj_details = response.json()
            proj_id = proj_details.get('id', "")
            return proj_id
    except Exception  as e:
        print(f"Failed to get get project Id {target_project_name} : {e}")
    
def get_wiki_id(ado_server_url, project_name, pat):
    try:
        wiki_api_url = f"{ado_server_url}/{project_name}/_apis/wiki/wikis?api-version=6.0"
        response = requests.get(wiki_api_url, auth=HTTPBasicAuth("", pat))
        if response.status_code == 200:
            wikis = response.json().get("value", [])
            if wikis:
                return wikis[0].get("id", "")  # Return the first wiki ID found
            else:
                print(f"No wikis found for project {project_name}")
                return None
        else:
            print(f"Failed to fetch wikis for project {project_name}. HTTP Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error occurred while fetching wiki ID: {e}")
        return None
    
def get_identities(source_disp_name): 
    try:
        read_identities_url = (
                    f"{target_ado_server_url}/{proj_id}/_api/_security/ReadExplicitIdentitiesJson"
                    f"?__v=5&permissionSetId={permission_set_id}"
                    f"&permissionSetToken=repoV2%2F{proj_id}/{wiki_id}/"
                )
        response = requests.get(
            read_identities_url,
            auth=HTTPBasicAuth("", target_pat)
        )
        if response.status_code == 200:
            identities = response.json().get("identities", [])
            for identity in identities:
                name = identity.get("FriendlyDisplayName", "")
                if source_disp_name == name:
                    TeamFoundationId = identity.get("TeamFoundationId", "")
                    return TeamFoundationId
    except Exception as e:
        print(f"Error in fetching the tfid of {source_disp_name} : {e}")
        return
                
def get_permission_descriptor_custom(tfid):
    try:
        display_permissions_url = (
                        f"{target_ado_server_url}/{proj_id}/_api/_security/DisplayPermissions?__v=5&tfid="
                        f"{tfid}"
                        f"&permissionSetId={permission_set_id}"
                        f"&permissionSetToken={urllib.parse.quote(f'repoV2/{proj_id}/{wiki_id}/')}"
                    )
        response = requests.get(
            display_permissions_url,
            auth=HTTPBasicAuth("", target_pat)
        )

        if response.status_code == 200:
            data = response.json()
            descriptor = data.get("descriptorIdentifier","")
            descriptoeType = data.get("descriptorIdentityType", "")
            permissions = data.get("permissions",[])
            updates =[]
            for permission in permissions[3:]:
                permission_= "Allow"
                if permission_ == "Allow (inherited)":
                    permissionId = 3
                elif permission_ == "Deny":
                    permissionId =2
                elif permission_ == "Not set":
                    permissionId = 0
                else:
                    permissionId =1
                updates.append({
                "PermissionId": permissionId ,
                "PermissionBit":permission.get("permissionBit",""),
                "NamespaceId": permission.get("namespaceId",""),
                "Token": permission.get("permissionToken","")
            })
                break
            return updates   
    except Exception as e:
        print(f"Error in fetching the descriptor for custom Team/Group/User : {e}")
        return            
            
def get_permission_descriptor(tfid, permissions_grp):
    try:
        display_permissions_url = (
                        f"{target_ado_server_url}/{proj_id}/_api/_security/DisplayPermissions?__v=5&tfid="
                        f"{tfid}"
                        f"&permissionSetId={permission_set_id}"
                        f"&permissionSetToken={urllib.parse.quote(f'repoV2/{proj_id}/{wiki_id}/')}"
                    )
        response = requests.get(
            display_permissions_url,
            auth=HTTPBasicAuth("", target_pat)
        )

        if response.status_code == 200:
            data = response.json()
            descriptor = data.get("descriptorIdentifier","")
            descriptoeType = data.get("descriptorIdentityType", "")
            permissions = data.get("permissions",[])
            updates =[]
            i=0
            for permission in permissions[3:]:
                permission_= permissions_grp[i]
                if permission_ == "Allow (inherited)":
                    permissionId = 3
                elif permission_ == "Deny":
                    permissionId =2
                elif permission_ == "Not set":
                    permissionId = 0
                else:
                    permissionId =1
                updates.append({
                "PermissionId": permissionId ,
                "PermissionBit":permission.get("permissionBit",""),
                "NamespaceId": permission.get("namespaceId",""),
                "Token": permission.get("permissionToken","")
            })
                i=i+1
            return updates , descriptoeType ,descriptor 
    except Exception as e:
        print(f"Error in fetching the descriptor for Team/Group/User : {e}")
        return "","",""

# Function to get Project Descriptor
def get_project_descriptor( ):
    try:
        target_ado_server_url_ = target_ado_server_url.replace("dev.azure.com", "vssps.dev.azure.com")
        url = f"{target_ado_server_url_}/_apis/graph/descriptors/{proj_id}?api-version=7.0"
        response = requests.get(url, auth=HTTPBasicAuth('', target_pat))
        if response.status_code == 200:
            data = response.json()
            print(url)
            project_descriptor = data["value"]
            return project_descriptor
        else:
            print(f"Failed to fetch project descriptor: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Failed to fetch project descriptor: {response.status_code} - {response.text}")
        return None

# Function to fetch all groups in the project
def get_project_groups( project_descriptor, pat, source_grp):
    try:
        target_ado_server_url_ = target_ado_server_url.replace("dev.azure.com", "vssps.dev.azure.com")
        url = f"{target_ado_server_url_}/_apis/graph/groups?scopeDescriptor={project_descriptor}&api-version=7.0-preview.1"
        response = requests.get(url, auth=HTTPBasicAuth('', target_pat))
        if response.status_code == 200:
            data = response.json()
            group_count = data["count"]
            if group_count > 0:
                groups = data["value"]
                for group in groups:
                    target_displayName = group.get("displayName","")
                    originId = group.get("originId","")
                    if target_displayName == source_grp:
                        return target_displayName ,originId 
            return 
        else:
            print(f"Failed to fetch project groups: {response.status_code} - {response.text}")
            return []  
    except Exception as e:
        print(f"Failed to fetch project groups: {response.status_code} - {e}")
        return []  
    
def get_originId_user(user):
    try:
        target_ado_server_url_ = target_ado_server_url.replace("dev.azure.com","vsaex.dev.azure.com")
        url = f"{target_ado_server_url_}/_apis/userentitlements?top={1000}&api-version=5.1-preview.2"
        response = requests.get(url , auth=HTTPBasicAuth("",target_pat))
        if response.status_code ==200:
            data =response.json()
            members = data["members"]
            for member in members:
                target_user = member.get("user")                
                dispName = target_user.get("displayName","")
                originId = target_user.get("originId","")
                if dispName == user:
                    return dispName , originId
        return False, False
    except Exception as e:
        print(f"Error in fectching the originId {e}")
        return False, False

def add_user_security(originId , target_user):
        url =f"{target_ado_server_url}/{proj_id}/_api/_security/AddIdentityForPermissions?__v=5"
        temp= f"[\"{originId}\",\"{originId}\"]"
        payload = {"newUsersJson":"[]","existingUsersJson":f"{temp}"}
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            url,
            auth=HTTPBasicAuth("", target_pat),
            headers=headers,
            data=json.dumps(payload)
        )
        if response.status_code ==200:
            data = response.json()
            AddIdentities = data['AddedIdentity']
            descriptor_type = AddIdentities.get("DescriptorIdentityType","")
            descriptor = AddIdentities.get("DescriptorIdentifier","")
            tfid = AddIdentities.get("TeamFoundationId","")
            updates =get_permission_descriptor_custom(tfid)
            payload = get_payload(updates, descriptor_type, descriptor,tfid)
            result = migrate_permissions(payload)

def get_payload(updates , descriptor_type , descriptor, tfid):
    payload = {
                "TeamFoundationId": tfid,
                "DescriptorIdentityType": descriptor_type,
                "DescriptorIdentifier": descriptor,
                "PermissionSetId": permission_set_id,
                "PermissionSetToken": f"repoV2/{proj_id}/{wiki_id}/",
                "Updates": updates
                }
    return payload
                  
                        
if __name__ == "__main__":
    try:
        permission_set_id = "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        # Read input data from Excel input file
        input_file = 'wikis_input.xlsx'
        input_data = pd.read_excel(input_file)

        for _, row in input_data.iterrows():
            ado_server_url = str(row['Source_URL']).strip()
            pat = str(row['Source_PAT']).strip()
            project_name = str(row['Source_Project']).strip()
            target_ado_server_url = str(row['Target_URL']).strip()
            target_pat = str(row['Target_PAT']).strip()
            target_project_name = str(row['Target_Project']).strip()
            if not target_project_name or target_project_name == "nan":
                print("Warning: Skipping row due to missing project name.")
            source_discovery = "source_wiki_permissions.xlsx"
            target_discovery = "target_wiki_permissions.xlsx"
            source_df = pd.read_excel(source_discovery, sheet_name=None)  # Read all sheets
        
            print(f"Processing {project_name}")
            source_sheet = pd.DataFrame(source_df[project_name])

            proj_id = get_proj_details(target_ado_server_url, target_pat, target_project_name)
            wiki_id = get_wiki_id(target_ado_server_url, target_project_name , target_pat)
            
            list_groups = [
                "Project Collection Administrators",
                "Project Collection Build Service Accounts",
                "Project Collection Service Accounts",
                "Build Administrators",
                "Contributors",
                "Project Administrators",
                "Readers"
            ]

            for group , permission in source_sheet.iloc[:, 1:].items():
                group = str(group)
                print(group)
                permission =permission
                isUser = group.__contains__("(User)")
                if isUser:
                    user = group.replace("(User)","")
                    if user.__contains__("CatCore Build Service "):
                            collection = target_ado_server_url.split('/')[-1]
                            user = f"CatCore Build Service ({collection})"
                    target_username , originId = get_originId_user(user)
                    # if ((target_username is not False) or (user == f"CatCore Build Service ({collection})")):
                    if (user == f"CatCore Build Service ({collection})"):
                        if originId is not False:
                            add_user_security(originId, target_username)
                        tfid = get_identities(user)
                        updates , descriptor_type , descriptor =get_permission_descriptor(tfid , permission)
                        payload = get_payload(updates, descriptor_type, descriptor, tfid)
                        result =migrate_permissions(payload)
                else:
                    if group not in list_groups:
                        print("Fetching project descriptor...")
                        project_descriptor = get_project_descriptor( )

                        if project_descriptor:
                            group_name , originId = get_project_groups(project_descriptor, pat , group)
                            if group_name:
                                url =f"{target_ado_server_url}/{proj_id}/_api/_security/AddIdentityForPermissions?__v=5"
                                payload = {"newUsersJson":"[]","existingUsersJson":f"[\"{originId}\"]"}
                                headers = {"Content-Type": "application/json"}
                                response = requests.post(
                                    url,auth=HTTPBasicAuth("", target_pat),
                                    headers=headers,data=json.dumps(payload)
                                )
                                data = response.json()
                                AddIdentities = data['AddedIdentity']
                                descriptor_type = AddIdentities.get("DescriptorIdentityType","")
                                descriptor = AddIdentities.get("DescriptorIdentifier","")
                                tfid = AddIdentities.get("TeamFoundationId","")
                                updates =get_permission_descriptor_custom(tfid)
                                payload = get_payload(updates , descriptor_type , descriptor, tfid)
                                result = migrate_permissions(payload)

                        else:
                            print("Unable to fetch project descriptor. Exiting.")

                    tfid = get_identities(group)
                    updates , descriptor_type , descriptor =get_permission_descriptor(tfid , permission)
                    payload =get_payload(updates , descriptor_type , descriptor, tfid)
                    result =migrate_permissions(payload)
    except Exception as e:
        print(f"Error occured {e}")


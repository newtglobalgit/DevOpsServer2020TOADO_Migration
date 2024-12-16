import requests
import json
import base64


def add_comment_to_wiki_page(org_url, project_id, wiki_id, page_id, pat,comment_text):
    # Construct the API URL
    api_url = f"{org_url}/{project_id}/_apis/wiki/wikis/{wiki_id}/pages/{page_id}/comments"
    params = {
        "$top": "10",
        "excludeDeleted": "true",
        "$expand": "9",
        "api-version": "7.1"
    }

    # Encode the PAT for basic authentication
    encoded_pat = base64.b64encode(f":{pat}".encode('utf-8')).decode('utf-8')

    # Set up headers with the encoded PAT for authentication
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_pat}"
    }

    # Set up the body for the request
    data = {
        "text": comment_text
    }

    # Send the POST request to Azure DevOps
    response = requests.post(api_url, params=params, headers=headers, data=json.dumps(data))

    # Check for success
    if response.status_code == 200:
        print("Comment successfully added!")
    else:
        print(f"Failed to add comment. Status code: {response.status_code}")
        print(response.text)
    
    return response.json() if response.status_code == 200 else {"error": response.text}

# Example usage of the function
if __name__ == "__main__":
    org_url = "https://dev.azure.com/AdoMigrateorg"
    wiki_id = "1b826377-6247-47e5-90fc-38449eb0d7a8"
    page_id = "79"
    pat = "7rHbuHSAloiXkG5cSAsUtoQKKjobc7OJuwxeRnuvXwISQ9CTidyKJQQJ99ALACAAAAA7b41nAAAGAZDOUqcB"
    api_version = "7.1"
    comment_text = "hi"
    project_id = "892dce1a-81c8-4b6b-bf0d-c4851609a01b"

    response = add_comment_to_wiki_page(
        org_url, project_id, wiki_id, page_id, pat, api_version, comment_text
    )
    print(response)

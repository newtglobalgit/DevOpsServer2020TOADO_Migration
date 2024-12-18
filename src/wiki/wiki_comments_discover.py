import requests
from requests.auth import HTTPBasicAuth
import xlsxwriter

# Azure DevOps Server API details

version = "wikiMaster"  # Assuming you're interested in the master version



# Function to fetch the page ID based on the path
def get_page_id(server_url,project_id,wiki_id,username,pat,path):
    # Build the API URL to get the wiki page details
    api_url = f"{server_url}/{project_id}/_apis/wiki/wikis/{wiki_id}/pages?path={path}&recursionLevel=0&versionDescriptor.version={version}&includeContent=true"
    
    # Make the GET request to fetch the wiki page details
    response = requests.get(api_url, auth=HTTPBasicAuth(username, pat))
    
    if response.status_code == 200:
        wiki_data = response.json()
        
        # Extract the page ID from the response
        page_id = wiki_data.get('id', 'N/A')
        
        if page_id != 'N/A':
            print(f"Page ID fetched: {page_id}")
            return page_id
        else:
            print("Page ID not found in the response.")
            return None
    else:
        print(f"Failed to fetch wiki page details. Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

# Function to get Wiki Comments for the Page
def get_wiki_comments(server_url, project_id, wiki_id, page_id, username, pat):
    result = []
    
    if not page_id:
        print("Invalid page ID. Cannot fetch comments.")
        return result
    
    # Initialize variables for pagination
    continuation_token = None
    comments_api_url = f"{server_url}/{project_id}/_apis/wiki/wikis/{wiki_id}/pages/{page_id}/comments"
    
    # Create an Excel workbook and worksheet
    workbook = xlsxwriter.Workbook('wiki_comments.xlsx')
    worksheet = workbook.add_worksheet()
    
    # Define headers for the Excel file
    worksheet.write(0, 0, 'Comment ID')
    worksheet.write(0, 1, 'Comment Text')
    worksheet.write(0, 2, 'Created By')
    worksheet.write(0, 3, 'Created Date')
    
    row = 1  # Start writing data from row 1
    
    while True:
        # Add query parameters for pagination
        params = {
            'excludeDeleted': 'true',
            '$expand': '9',
            'continuationToken': continuation_token
        }
        
        # Make the GET request to fetch comments
        response = requests.get(comments_api_url, params=params, auth=HTTPBasicAuth(username, pat))
        
        if response.status_code == 200:
            # Parse the JSON response
            comments_data = response.json()
            comments = comments_data.get('comments', [])
            
            # Append the fetched comments to the result list
            for comment in comments:
                comment_id = comment.get('id', 'N/A')
                comment_text = comment.get('text', 'No Text')
                created_by = comment.get('createdBy', {}).get('displayName', 'Unknown')
                created_date = comment.get('createdDate', 'Unknown Date')

                result.append({
                    "comment_id": comment_id,
                    "comment_text": comment_text,
                    "created_by": created_by,
                    "created_date": created_date
                })
                
                # Write comment details to the Excel file
                worksheet.write(row, 0, comment_id)
                worksheet.write(row, 1, comment_text)
                worksheet.write(row, 2, created_by)
                worksheet.write(row, 3, created_date)
                row += 1
            
            # Check if there is a continuation token for the next page
            continuation_token = comments_data.get('continuationToken', None)
            
            if not continuation_token:
                # No more pages to fetch
                break
        else:
            print(f"Failed to fetch comments. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            break
    
    # Close the workbook after writing the data
    workbook.close()
    print("Comments exported to 'wiki_comments.xlsx'.")
    
    return result

# Main execution flow
if __name__ == "__main__":
    # Fetch Page ID dynamically from the path
    page_id = get_page_id(path)
    
    if page_id:
        # Get Comments for the given Page ID
        get_wiki_comments(page_id)

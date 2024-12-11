 

import pandas as pd
import sys
import os



# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.dbDetails.migration_details_db import db_post_migration_details , db_get_migration_details

config_df = pd.read_excel(f'src\pipeline\credentials.xlsx')
for index, row in config_df.iterrows():
        # Extract values from the current row
        source_instance = row['Source_URL']
        source_project_name = row['Source_Project']
        # source_username = row['Username']
        source_pat = row['Source_Pat']
        target_instance =row["Target_URL"]
        target_project_name = row["Target_Project"]
        target_pat =  row["Target_Pat"]

        data ={
           "source_server_url" : source_instance,
            "source_project_name" : source_project_name,
            "source_pat" :source_pat,
            "target_organization_url" : target_instance,
            "target_project_name" :target_project_name,
            "target_pat" :target_pat,
        }

        db_post_migration_details(data)

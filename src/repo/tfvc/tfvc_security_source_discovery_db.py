import sys
import os
import logging
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError


# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.dbDetails.db import SessionLocal, logger
from src.models.tfvc_security_source_discovery_model import TFVCSecuritySourceDetails


def db_post_tfvc_security(data):
    db = None  
    try:
        collection_name = data.get("collection_name",""), 
        project_name =data.get("project_name",""), 
        tfvc_name = data.get("tfvc_name","") , 
        tfvc_branch_name = data.get("tfvc_branch_name",""), 
        permission_type = data.get("permission_type",""), 
        permission_name = data.get("permission_name",""), 
        access_type =data.get("access_type","") , 
        access_level = data.get("access_level","") 


        if not project_name:
            raise ValueError("Project name and collection name are required fields.")

        # Log the data being inserted
        logging.info(
            f"Inserting record: \
            collection_name = {collection_name},\
            project_name ={project_name},\
            tfvc_name = {tfvc_name} ,\
            tfvc_branch_name ={tfvc_branch_name},\
            permission_type = {permission_type},\
            permission_name = {permission_name},\
            access_type = {access_type} ,\
            access_level = {access_level} "
            )


        # Create a new record
        new_record = TFVCSecuritySourceDetails(
           collection_name = collection_name,
            project_name =project_name,
            tfvc_name = tfvc_name ,
            tfvc_branch_name =tfvc_branch_name,
            permission_type = permission_type,
            permission_name = permission_name,
            access_type = access_type ,
            access_level = access_level
        )

        # Insert into the database
        with SessionLocal() as db:
            query = db.add(new_record)
            
            db.commit()
      
        # Log success response
        success_message = "Record created successfully for the tfvc security."
        logging.info(success_message)

    except ValueError as ve:
        # Handle input validation errors and log them
        error_message = f"Input validation failed: {str(ve)}"
        logging.error(error_message)

    except Exception as e:
        # Handle database or unexpected errors and log them
        print(str(e))
        error_message = f"Unexpected error occurred: {str(e)}"
        logging.error(error_message)

    finally:
        if db:
            db.close()  # Ensure the connection is closed

def db_get_tfvc_security():
    db = None
    try:
        with SessionLocal() as db:
            
            records = db.query(TFVCSecuritySourceDetails).all()
            
            if records:
                logging.info("Records retrieved successfully:")
                for record in records:
                    logging.info(record.to_dict())  
                return records
            else:
                # Log if no record found
                logging.info("No records found in the table.")
                return None
    except SQLAlchemyError as sae:
        # Handle database errors and log them
        error_message = f"Database error occurred: {str(sae)}"
        logging.error(error_message)
        return None
    except Exception as e:
        # Handle unexpected errors and log them
        error_message = f"Unexpected error occurred: {str(e)}"
        logging.error(error_message)
        return None

    finally:
        if db:
            db.close()  # Ensure the connection is closed


# Main method to simulate data entry
def main():
    # Sample data to be inserted (you can adjust it as needed)
    data = {
        "collection_name" : "Default",
        "project_name" : "CatCore",
        "tfvc_name" : "CatCore" ,
        "tfvc_branch_name" : "$/CatCore",
        "permission_type" : "User",
        "permission_name" : "Build Administrator",
        "access_type" : "Rename" ,
        "access_level" :" Deny"
        }
    # # data =["qaserver","1","qaserver","2024-12-07T06:31:38.31Z","azure-pipelines.yml",0,0,"TfsGit","qaserver","refs/heads/master",
    # #            "No (Build)","Default",'','','','',1,'']
    # # data =["qaserver","1","qaserver"]

    # # Call db_post_workitem function to insert data
    db_post_tfvc_security(data)
    results =db_get_tfvc_security()
    for result in results:
        print(result.pipeline_id)
    print(results)
    


# Entry point of the script
if __name__ == "__main__":
    main()
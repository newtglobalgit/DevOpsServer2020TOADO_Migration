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
from src.models.build_pipeline_mapping_model import  BuildPipelineMappingDetails


def db_post_build_pipeline_mapping(data):
    db = None  
    try:
        mapping_pipelines_id = data.get("mapping_pipelines_id",0)
        source_project_name = data.get("Source_Project","")
        source_pipeline_name = data.get("Source_Pipeline_Name","")
        source_pipeline_id = data.get("Source_Pipeline_Id",0)
        source_file_name =data.get("File_Name","")
        source_repository_name =data.get("Source_Repo_Name","")
        source_repository_branch =data.get("Source_Repo_Branch","")
        target_project_name =data.get("Source_Project","")
        target_pipeline_name = data.get("Source_Pipeline_Name","")
        is_classic = data.get("Is_Classic","")
        migration_required =data.get("Migration_Required","")
        status = data.get("Status","")

        if not source_project_name:
            raise ValueError("Project name and collection name are required fields.")

        # Log the data being inserted
        logging.info(
            f"Inserting record: \
            source_project_name = {source_project_name},\
        source_pipeline_name = {source_pipeline_name},\
        source_pipeline_id = {source_pipeline_id},\
        source_file_name ={source_file_name},\
        source_repository_name ={source_repository_name},\
        source_repository_branch ={source_repository_branch},\
        target_project_name = {target_project_name},\
        target_pipeline_name = {target_pipeline_name},\
        is_classic = {is_classic},\
        migration_required ={migration_required},\
        status = {status},\
            ")


        # Create a new record
        new_record = BuildPipelineMappingDetails(
             source_project_name = source_project_name,
        source_pipeline_name = source_pipeline_name,
        source_pipeline_id = source_pipeline_id,
        source_file_name =source_file_name,
        source_repository_name =source_repository_name,
        source_repository_branch =source_repository_branch,
        target_project_name = target_project_name,
        target_pipeline_name = target_pipeline_name,
        is_classic = is_classic,
        migration_required =migration_required,
        status = status
        )

        # Insert into the database
        with SessionLocal() as db:
            query = db.add(new_record)
            
            db.commit()
      
        # Log success response
        success_message = "Record created successfully for the build pipeline."
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

def db_get_build_pipeline():
    db = None
    try:
        with SessionLocal() as db:
            
            records = db.query(BuildPipelineDetails).all()
            
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
    # data = {
    #     "project_name":"qaserver",
    #         "pipeline_id":'1',
    #         "pipeline_name":"qaserver",
    #         "last_updated_date":"2024-12-07T06:31:38.31Z",
    #         "file_name":"azure-pipelines.yml",
    #         "variables":0,
    #         "variable_groups":0,
    #         "repository_type":"TfsGit",
    #         "repository_name":"qaserver",
    #         "repository_branch":"refs/heads/master",
    #         "classic_pipeline":"No (Build)",
    #         "agents":"Default",
    #         "phases":'',
    #         "execution_type":'',
    #         "max_concurrency":0,
    #         "continue_on_error": '',
    #         "builds":1,
    #         "artifacts":''
    #     }
    # # data =["qaserver","1","qaserver","2024-12-07T06:31:38.31Z","azure-pipelines.yml",0,0,"TfsGit","qaserver","refs/heads/master",
    # #            "No (Build)","Default",'','','','',1,'']
    # # data =["qaserver","1","qaserver"]

    # # Call db_post_workitem function to insert data
    # db_post_build_pipeline(data)
    results =db_get_build_pipeline()
    for result in results:
        print(result.pipeline_id)
    print(results)
    


# Entry point of the script
if __name__ == "__main__":
    main()
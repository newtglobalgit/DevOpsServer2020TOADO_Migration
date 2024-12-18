import sys
import os
import logging
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd


# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.dbDetails.db import SessionLocal, logger
from src.models.wiki_target_model import  WikiDetails


def db_post_wiki(data):
    db = None  
    try:
        collection_name= data.get("collection_name","")
        project_id=data.get("project_id","")
        wiki_id=data.get("wiki_id","")
        project_name = data.get("project_name", "")
        file_path = data.get("file_path", "")
        size_bytes = data.get("size_bytes", "")
        logging.debug(f"Size bytes received: {size_bytes}")
        last_modified = data.get("last_modified", None)
        page_id=data.get("page_id","")


        if not file_path:
            raise ValueError("File path is a required field.")

        # Log the data being inserted
        logging.info(
            f"Inserting record: \
            collection_name={collection_name} \
            project_id={project_id} \
            project_name={project_name} \
            wiki_id={wiki_id} \
            file_path={file_path},\
            size_bytes={size_bytes},\
            page_id={page_id},\
            last_modified={last_modified}"
        )


        # Create a new record
        new_record = WikiDetails(
            collection_name=collection_name,
            project_id=project_id,
            wiki_id=wiki_id,
            project_name=project_name,
            file_path=file_path,
            size_bytes=size_bytes,
            last_modified=last_modified,
            page_id=page_id
        )

         # Insert into the database
        with SessionLocal() as db:
            db.add(new_record)
            db.commit()
      
        # Log success response
        success_message = "Record created successfully for the wiki."
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


def db_get_wiki():
    db = None
    try:
        with SessionLocal() as db:
            records = db.query(WikiDetails).all()
            
            if records:
                logging.info("Records retrieved successfully:")
                result = []
                for record in records:
                    result.append(record.to_dict())
                    logging.info(record.to_dict())  
                return pd.DataFrame(result)
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
        print(e)
        logging.error(error_message)
        return None

    finally:
        if db:
            db.close()  # Ensure the connection is closed


# # Main method to simulate data entry
# def main():
#     # Sample data to be inserted (you can adjust it as needed)
#     data = {
#         "project_name":"qaserver",
#             "pipeline_id":'1',
#             "pipeline_name":"qaserver",
#             "last_updated_date":"2024-12-07T06:31:38.31Z",
#             "file_name":"azure-pipelines.yml",
#             "variables":0,
#             "variable_groups":0,
#             "repository_type":"TfsGit",
#             "repository_name":"qaserver",
#             "repository_branch":"refs/heads/master",
#             "classic_pipeline":"No (Build)",
#             "agents":"Default",
#             "phases":'',
#             "execution_type":'',
#             "max_concurrency":0,
#             "continue_on_error": '',
#             "builds":1,
#             "artifacts":''
#         }
#     # data =["qaserver","1","qaserver","2024-12-07T06:31:38.31Z","azure-pipelines.yml",0,0,"TfsGit","qaserver","refs/heads/master",
#     #            "No (Build)","Default",'','','','',1,'']
#     # data =["qaserver","1","qaserver"]

#     # Call db_post_workitem function to insert data
#     db_post_build_pipeline(data)
#     db_get_build_pipeline()
    


# # Entry point of the script
# if __name__ == "__main__":
#     main()

print(db_get_wiki())
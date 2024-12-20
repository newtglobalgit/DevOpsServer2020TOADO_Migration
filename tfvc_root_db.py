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
from src.models.tfvc_root_model import  TfvcRootDetails


def db_post_tfvc_root(data):
    db = None  
    try:
        collection_name = data.get("collection_name","")
        project_name = data.get("project_name","")
        branch_name = data.get("branch_name","")
        root_folder =data.get("root_folder","")
        project_folder =data.get("project_folder","")
        file_name =data.get("file_name","")
        file_type =data.get("file_type","")
        file_size =data.get("file_size","")
        file_path =data.get("file_path","")
        


        if not file_path:
            raise ValueError("File path is a required field.")

        # Log the data being inserted
        logging.info(
            f"Inserting record: \
            collection_name={collection_name}, \
            project_name={project_name}, \
            branch_name={branch_name}, \
            root_folder={root_folder}, \
            project_folder={project_folder}, \
            file_name={file_name}, \
            file_type={file_type}, \
            file_size={file_size}, \
            file_path={file_path}"
        )


        # Create a new record
        new_record = TfvcRootDetails(
            collection_name = collection_name,
            project_name = project_name,
            branch_name = branch_name,
            root_folder = root_folder,
            project_folder = project_folder,
            file_name = file_name,
            file_type = file_type,
            file_size = file_size,
            file_path = file_path,
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


def db_get_tfvc_root():
    db = None
    try:
        with SessionLocal() as db:
            records = db.query(TfvcRootDetails).all()
            
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



print(db_get_tfvc_root())
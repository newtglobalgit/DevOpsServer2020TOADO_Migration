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
from src.models.tfvc_all_changeset_model import TfvcAllChangesetDetails


def db_post_tfvc_allchangeset(data):
    db = None  
    try:
        collectionname = data.get("collectionname","")
        projectname = data.get("projectname","")
        branchname = data.get("branchname","")
        changesetid =data.get("changesetid","")
        author =data.get("author","")
        timedate =data.get("timedate","")
        comment =data.get("comment","")
        


        

        # Log the data being inserted
        logging.info(
            f"Inserting record: \
            collectionname={collectionname}, \
            projectname={projectname}, \
            branchname={branchname}, \
            changesetid={changesetid}, \
            author={author}, \
            timedate={timedate}, \
            comment={comment}"
        )


        # Create a new record
        new_record = TfvcAllChangesetDetails(
            collectionname = collectionname,
            projectname = projectname,
            branchname = branchname,
            changesetid = changesetid,
            author = author,
            timedate = timedate,
            comment = comment
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


def db_get_tfvc_allchangeset():
    db = None
    try:
        with SessionLocal() as db:
            records = db.query(TfvcAllChangesetDetails).all()
            
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



print(db_get_tfvc_allchangeset())
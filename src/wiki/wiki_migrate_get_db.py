import sys
import os
import logging
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.dbDetails.db import SessionLocal, logger
from src.models.migration_details_model import MigrationDetails

# Define the output Excel file path
OUTPUT_FILE = "wiki_migrate_input.xlsx"

def db_get_wiki():
    db = None
    try:
        # Initialize database session
        with SessionLocal() as db:
            # Fetch all records from the MigrationDetails table
            records = db.query(MigrationDetails).all()

            if records:
                logging.info("Records retrieved successfully:")
                result = []
                for record in records:
                    result.append(record.to_dict())  # Convert records to dictionaries
                    logging.info(record.to_dict())  # Log each record as a dictionary

                # Convert the result list to a DataFrame
                df = pd.DataFrame(result)

                # Save the DataFrame to an Excel file
                df.to_excel(OUTPUT_FILE, index=False, engine="xlsxwriter")
                logging.info(f"Data successfully exported to {OUTPUT_FILE}")

                return df
            else:
                # Log if no records found
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

# Fetch the data and create the Excel file
if __name__ == "__main__":
    df = db_get_wiki()
    if df is not None:
        print("Data exported to Excel successfully.")
    else:
        print("No data available or an error occurred.")

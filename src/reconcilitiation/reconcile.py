import os
from src.configuration.constants import ProjectConstants
from sqlalchemy import text
from src.dbDetails.db import get_db


class Reconcile:

    
    def __init__(self):
        
        print("Reconcile class initialized")

    '''
        Execute reconciliation for the given reconciliation item.
        param reconciliation_item: The item to reconcile.
    '''
    def execute_reconciliation(self, reconciliation_item: ProjectConstants ):

        constant_name = reconciliation_item.name
        
        print(f"Executing reconciliation for: {constant_name}")
        db = None
        try:

            # Get a database session
            db = next(get_db())

            # SQL to call the stored procedure
            sql = text("CALL execute_reconciliation(:constant_name, :output_data)")
        
            # Define output parameter as None initially
            output_data = None

            # Execute the stored procedure
            result = db.execute(sql, {"constant_name": constant_name, "output_data": output_data})

            # Fetch the result from the output parameter
            output = result.fetchone()[0]  # Assuming the procedure returns a single row

            print("Procedure Output:")
            print(output)

        except Exception as e:
            print(f"Error while calling procedure: {e}")

        finally:
            db.close()




    '''
        Generate data for the given reconciliation item.
    '''
    def generate_data(self, reconciliation_item: str):
        
        print(f"Generating data for: {reconciliation_item}")



# Creating an instance of the class
recon = Reconcile()


if __name__ == "__main__":
    #input_value = "Gopal Sharma"
    recon.execute_reconciliation(ProjectConstants.REPO_RECONCILITION)
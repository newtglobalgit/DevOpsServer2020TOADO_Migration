import pandas as pd
import psycopg2
from psycopg2 import sql
import os
import credentials

# Read the Excel file containing the reconciliation input form
def read_excel(file_path, sheet_name='Phase1'):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)  # Adjust sheet name if necessary
        print(f"Successfully read input form: {file_path}")
        return df
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        return None

# Read the sheet from the specified Excel file
def read_sheet(excel_path, sheet_name):
    try:
        # Ensure the path is correct and exists
        excel_path = os.path.abspath(excel_path.strip('"'))
        sheet_df = pd.read_excel(excel_path, sheet_name=sheet_name)
        print(f"Successfully read sheet {sheet_name} from {excel_path}")
        return sheet_df
    except Exception as e:
        print(f"Error reading sheet {sheet_name} from {excel_path}: {e}")
        return None

# Establish PostgreSQL connection
def connect_to_postgresql(dbname, user, password, host, port):
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        print(f"Successfully connected to PostgreSQL database: {dbname}")
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

# Create schema if it does not exist
def create_schema_if_not_exists(schema_name, conn):
    try:
        cursor = conn.cursor()
        create_schema_query = sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(schema_name))
        cursor.execute(create_schema_query)
        conn.commit()
        print(f"Schema {schema_name} ensured to exist")
    except Exception as e:
        print(f"Error creating schema {schema_name}: {e}")
        conn.rollback()
    finally:
        cursor.close()

# Infer PostgreSQL column types from pandas dtypes
def infer_column_types(df):
    dtype_mapping = {
        'int64': 'INTEGER',
        'float64': 'FLOAT',
        'bool': 'BOOLEAN',
        'datetime64[ns]': 'TIMESTAMP',
        'object': 'TEXT'
    }
    columns = []
    for col in df.columns:
        col_type = dtype_mapping.get(str(df[col].dtype), 'TEXT')
        columns.append(sql.Identifier(col) + sql.SQL(' ') + sql.SQL(col_type))
    return sql.SQL(', ').join(columns)

# Create table based on DataFrame
def create_table_from_dataframe(df, schema_name, table_name, conn):
    try:
        cursor = conn.cursor()
        # Infer column definitions
        columns = infer_column_types(df)
        create_table_query = sql.SQL('CREATE TABLE IF NOT EXISTS {}.{} ({})').format(
            sql.Identifier(schema_name),
            sql.Identifier(table_name),
            columns
        )
        cursor.execute(create_table_query)
        print(f"Table {schema_name}.{table_name} created successfully")
        conn.commit()
    except Exception as e:
        print(f"Error creating table {schema_name}.{table_name}: {e}")
        conn.rollback()
    finally:
        cursor.close()

# Insert data into the created table
def insert_data_into_table(df, schema_name, table_name, conn):
    try:
        cursor = conn.cursor()
        columns = [sql.Identifier(col) for col in df.columns]
        values = [sql.Placeholder() for _ in df.columns]
        insert_query = sql.SQL('INSERT INTO {}.{} ({}) VALUES ({})').format(
            sql.Identifier(schema_name),
            sql.Identifier(table_name),
            sql.SQL(', ').join(columns),
            sql.SQL(', ').join(values)
        )
        for row in df.itertuples(index=False, name=None):
            cursor.execute(insert_query, row)
        conn.commit()
        print(f"Data inserted into table {schema_name}.{table_name} successfully")
    except Exception as e:
        print(f"Error inserting data into table {schema_name}.{table_name}: {e}")
        conn.rollback()
    finally:
        cursor.close()

if __name__ == "__main__":
    # Update the file path and PostgreSQL connection details
    reconciliation_input_path = 'reconciliation_input_form.xlsx'
    postgres_user = credentials.user
    postgres_password = credentials.password
    postgres_host = credentials.host
    postgres_port = credentials.port

    # Read Excel file containing reconciliation input form
    input_df = read_excel(reconciliation_input_path)

    if input_df is not None:
        # Process each row in the input DataFrame
        for index, row in input_df.iterrows():
            excel_path = row['Excel Path'].strip('"')
            dbname = row['Reconciliation Type']
            schema_name = row['Node Point']
            tag = row['Tag']
            # Connect to PostgreSQL
            conn = connect_to_postgresql(dbname, postgres_user, postgres_password, postgres_host, postgres_port)
            if conn:
                # Ensure the schema exists
                create_schema_if_not_exists(schema_name, conn)
                for sheet_column in ['Sheet 1', 'Sheet 2', 'Sheet 3', 'Sheet 4']:
                    if pd.notna(row[sheet_column]):
                        sheet_name = row[sheet_column]
                        table_name = f"{sheet_name}_{tag}"
                        sheet_df = read_sheet(excel_path, sheet_name)
                        if sheet_df is not None:
                            create_table_from_dataframe(sheet_df, schema_name, table_name, conn)
                            insert_data_into_table(sheet_df, schema_name, table_name, conn)
                # Close the connection
                conn.close()
                print(f"PostgreSQL connection to {dbname} closed.")
    else:
        print("Failed to read the reconciliation input form.")

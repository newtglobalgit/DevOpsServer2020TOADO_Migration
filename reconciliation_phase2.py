import pandas as pd
import psycopg2
from psycopg2 import sql
import os
import credentials
import re
from datetime import datetime
import getpass
import xlsxwriter

# Function to convert column names to upper camel case and replace underscores with spaces
def to_upper_camel_case(column_name):
    words = column_name.split('_')
    return ' '.join(word.capitalize() for word in words)

# Read the Excel file containing the reconciliation input form
def read_excel(file_path, sheet_name='Phase2'):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"Successfully read input form: {file_path}")
        return df
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
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

# Find tables in the specified schema that match the tag and count their rows
def find_tables_and_counts(schema_name, tag, conn):
    try:
        cursor = conn.cursor()
        query = sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_name LIKE %s")
        cursor.execute(query, (schema_name, f"%{tag}%"))
        tables = cursor.fetchall()
        
        table_counts = {}
        for table in tables:
            table_name = table[0]
            # Remove the tag from the table name
            base_table_name = re.sub(f"-?{tag}$", "", table_name)
            count_query = sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                sql.Identifier(schema_name),
                sql.Identifier(table_name)
            )
            cursor.execute(count_query)
            count = cursor.fetchone()[0]
            table_counts[base_table_name] = count
        
        cursor.close()
        return table_counts
    except Exception as e:
        print(f"Error finding tables and counts in schema {schema_name}: {e}")
        return {}

# Create reconciliation table with dynamic columns in correct order
def create_reconciliation_table(conn, source_tables, target_tables):
    try:
        cursor = conn.cursor()
        columns = [
            "source_collection TEXT",
            "source_project TEXT",
        ]

        for table in source_tables:
            col_name = f"source_git_{table.replace('-', '_')}_count INTEGER"
            columns.append(col_name)

        columns += [
            "target_organization TEXT",
            "target_project TEXT",
        ]

        for table in target_tables:
            col_name = f"target_git_{table.replace('-', '_')}_count INTEGER"
            columns.append(col_name)

        columns += [
            "status TEXT",
            "reconciliation_remarks TEXT",
            "customer_verification TEXT"
        ]

        create_table_query = f"CREATE TABLE IF NOT EXISTS reconciliation ({', '.join(columns)});"
        cursor.execute(create_table_query)
        conn.commit()
        print("Reconciliation table created successfully")
    except Exception as e:
        print(f"Error creating reconciliation table: {e}")
        conn.rollback()
    finally:
        cursor.close()

# Insert reconciliation data into the table
def insert_reconciliation_data(conn, data, columns):
    try:
        cursor = conn.cursor()
        insert_query = f"""
        INSERT INTO reconciliation ({', '.join(columns)})
        VALUES ({', '.join(['%s'] * len(columns))})
        """
        cursor.execute(insert_query, data)
        conn.commit()
        print("Reconciliation data inserted successfully")
    except Exception as e:
        print(f"Error inserting reconciliation data: {e}")
        conn.rollback()
    finally:
        cursor.close()

# Create and format Excel reconciliation report
def create_excel_report(df, target_project_name, dbname, input_df):
    folder_path = os.path.join(os.getcwd(), 'Reconciliation')
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{target_project_name}_{dbname}_reconciliation_report.xlsx")

    # Convert column names to upper camel case with spaces
    df.columns = [to_upper_camel_case(col) for col in df.columns]

    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Create Summary sheet
        summary_ws = workbook.add_worksheet('Summary')
        summary_ws.hide_gridlines(2)
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#000080',
            'border': 1
        })
        regular_format = workbook.add_format({
            'border': 1
        })

        summary_data = {
            'Report Title': f"{dbname} Reconciliation Report",
            'Purpose of the report': f"This report provides a summary and detailed view of the {dbname} reconciliation.",
            'Run Date': datetime.now().strftime('%d-%b-%Y %I:%M %p'),
            'Run Duration': str(datetime.now() - start_time),
            'Run By': getpass.getuser(),
            'Input': str(input_df.values)
        }

        row = 0
        for key, value in summary_data.items():
            summary_ws.write(row, 0, key, header_format)
            summary_ws.write(row, 1, value, regular_format)
            row += 1

        summary_ws.set_column(0, 0, 25.71)  # Adjust column A width
        summary_ws.set_column(1, 1, 76.87)  # Adjust column B width
        for i in range(len(summary_data)):
            summary_ws.set_row(i, 30)  # Adjust row height

        # Create Reconciliation Report sheet
        reconciliation_ws = workbook.add_worksheet('Reconciliation Report')
        reconciliation_ws.hide_gridlines(2)

        # Define header format
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#000080',
            'border': 1
        })
        data_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        empty_format = workbook.add_format({
            'border': 0,
            'align': 'center',
            'valign': 'vcenter'
        })

        # Write the header
        for col_num, column_title in enumerate(df.columns):
            reconciliation_ws.write(0, col_num, column_title, header_format)

        # Write the data
        for row_num, row_data in enumerate(df.values, 1):
            for col_num, cell_value in enumerate(row_data):
                reconciliation_ws.write(row_num, col_num, cell_value, data_format)

        # Apply empty format to the rest of the sheet
        for row in range(1, len(df) + 1):
            for col in range(len(df.columns)):
                if pd.isna(df.iloc[row - 1, col]):
                    reconciliation_ws.write(row, col, "", empty_format)

        # Adjust column widths
        for col_num, col in enumerate(df.columns):
            max_length = max([len(str(cell)) for cell in df[col].values] + [len(col)])
            adjusted_width = (max_length + 2)
            reconciliation_ws.set_column(col_num, col_num, adjusted_width)

        # Apply conditional formatting to the 'Status' column
        status_col_index = df.columns.get_loc("Status")
        reconciliation_ws.conditional_format(1, status_col_index, len(df), status_col_index, {
            'type': 'cell',
            'criteria': '==',
            'value': '"MATCHED"',
            'format': workbook.add_format({'bg_color': '#008000', 'font_color': 'white'})
        })
        reconciliation_ws.conditional_format(1, status_col_index, len(df), status_col_index, {
            'type': 'cell',
            'criteria': '==',
            'value': '"NOT MATCHED"',
            'format': workbook.add_format({'bg_color': '#800000', 'font_color': 'white'})
        })

    print(f"Excel reconciliation report created: {file_path}")

# Delete the reconciliation table from the database
def delete_reconciliation_table(conn):
    try:
        cursor = conn.cursor()
        delete_table_query = "DROP TABLE IF EXISTS reconciliation;"
        cursor.execute(delete_table_query)
        conn.commit()
        print("Reconciliation table deleted successfully")
    except Exception as e:
        print(f"Error deleting reconciliation table: {e}")
        conn.rollback()
    finally:
        cursor.close()

# Delete tables used for reconciliation from the database
def delete_reconciliation_tables(conn, schema_name, tag):
    try:
        cursor = conn.cursor()
        query = sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_name LIKE %s")
        cursor.execute(query, (schema_name, f"%{tag}%"))
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            drop_table_query = sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                sql.Identifier(schema_name),
                sql.Identifier(table_name)
                )
            cursor.execute(drop_table_query)

        conn.commit()
        print(f"Tables with tag '{tag}' in schema '{schema_name}' deleted successfully")
    except Exception as e:
        print(f"Error deleting tables in schema {schema_name} with tag {tag}: {e}")
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
        # Start timing the script
        start_time = datetime.now()

        # Process each row in the input DataFrame
        for index, row in input_df.iterrows():
            source_collection_name = row['Source Collection Name']
            source_project_name = row['Source Project Name']
            dbname = row['Reconciliation Type']
            tag = row['Tag']
            target_organization_name = row['Target Organization Name']
            target_project_name = row['Target Project Name']
            
            # Connect to PostgreSQL
            conn = connect_to_postgresql(dbname, postgres_user, postgres_password, postgres_host, postgres_port)
            if conn:
                # Find tables and counts in 'Source' schema
                source_table_counts = find_tables_and_counts('Source', tag, conn)
                source_columns = [f"source_git_{table.replace('-', '_')}_count" for table in source_table_counts.keys()]
                
                # Find tables and counts in 'Target' schema
                target_table_counts = find_tables_and_counts('Target', tag, conn)
                target_columns = [f"target_git_{table.replace('-', '_')}_count" for table in target_table_counts.keys()]

                # Ensure no duplicate columns
                source_columns = list(set(source_columns))
                target_columns = list(set(target_columns))

                # Determine status
                status = "MATCHED" if source_table_counts == target_table_counts else "NOT MATCHED"

                # Create reconciliation table with dynamic columns in correct order
                create_reconciliation_table(conn, source_table_counts.keys(), target_table_counts.keys())
                
                # Prepare reconciliation data
                data = [
                    source_collection_name,
                    source_project_name,
                ]

                for count in source_table_counts.values():
                    data.append(count)

                data += [
                    target_organization_name,
                    target_project_name,
                ]

                for count in target_table_counts.values():
                    data.append(count)

                data += [
                    status,
                    '',  # Reconciliation Remarks
                    ''   # Customer Verification
                ]

                columns = [
                    "source_collection",
                    "source_project",
                ] + source_columns + [
                    "target_organization",
                    "target_project",
                ] + target_columns + [
                    "status",
                    "reconciliation_remarks",
                    "customer_verification"
                ]

                # Insert reconciliation data
                insert_reconciliation_data(conn, data, columns)

                # Create DataFrame for Excel report
                reconciliation_df = pd.DataFrame([data], columns=columns)
                
                # Create Excel reconciliation report
                create_excel_report(reconciliation_df, target_project_name, dbname, input_df)

                # Delete the reconciliation table from the database
                delete_reconciliation_table(conn)
                
                # Delete tables used for reconciliation from the database
                delete_reconciliation_tables(conn, 'Source', tag)
                delete_reconciliation_tables(conn, 'Target', tag)
                
                # Close the connection
                conn.close()
                print(f"PostgreSQL connection to {dbname} closed.")
    else:
        print("Failed to read the reconciliation input form.")

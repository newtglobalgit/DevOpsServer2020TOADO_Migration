import pandas as pd

class ExcelReader:
    def __init__(self, file_path, sheet_name=None):
        """
        Initialize the ExcelReader class with the file path and sheet name.
        If sheet_name is None, it will read all sheets in the Excel file.

        :param file_path: Path to the Excel file
        :param sheet_name: Name of the sheet to read (optional)
        """
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.data = self._load_excel_data()

    def _load_excel_data(self):
        """ Load the data from the specified Excel sheet(s). """
        try:
            # Read the data from Excel
            if self.sheet_name:
                df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
            else:
                # Load all sheets
                df = pd.read_excel(self.file_path, sheet_name=None)
            return df
        except Exception as e:
            print(f"Error reading the Excel file: {e}")
            return None

    def get_dataframe(self):
        """ Return the data as a pandas DataFrame. """
        return self.data

    def get_sheet_names(self):
        """ Get the list of sheet names in the Excel file. """
        if isinstance(self.data, dict):
            return list(self.data.keys())  # If all sheets were read, return sheet names
        return [self.sheet_name] if self.sheet_name else []

    def get_column_names(self):
        """ Get the column names of the data. """
        if isinstance(self.data, pd.DataFrame):
            return self.data.columns.tolist()
        elif isinstance(self.data, dict):
            # Return columns of each sheet
            return {sheet_name: data.columns.tolist() for sheet_name, data in self.data.items()}
        return []

    def get_data_as_dict(self):
        """ Convert the data to a list of dictionaries (rows). """
        if isinstance(self.data, pd.DataFrame):
            return self.data.to_dict(orient='records')
        elif isinstance(self.data, dict):
            # Return rows of each sheet as a list of dictionaries
            return {sheet_name: data.to_dict(orient='records') for sheet_name, data in self.data.items()}
        return []

    def get_data_as_list(self):
        """ Convert the data to a list of lists (rows). """
        if isinstance(self.data, pd.DataFrame):
            return self.data.values.tolist()
        elif isinstance(self.data, dict):
            # Return rows of each sheet as a list of lists
            return {sheet_name: data.values.tolist() for sheet_name, data in self.data.items()}
        return []

    def filter_data(self, condition):
        """ Filter the data based on a condition. """
        if isinstance(self.data, pd.DataFrame):
            return self.data[condition]
        elif isinstance(self.data, dict):
            return {sheet_name: data[condition] for sheet_name, data in self.data.items()}
        return []

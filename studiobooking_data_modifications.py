from openpyxl import load_workbook
import pandas as pd
import xlrd
from os import listdir
import os
import csv
import logging
import re 
from datetime import datetime


class FeatureFlags:
    def __init__(self):
        # May want to implement additional checks shown here: https://stackoverflow.com/questions/63116419/evaluate-boolean-environment-variable-in-python
        # Retrieves the .env variable if present, else returns False, lowercases all and verifies one of the strings is a true value. 
        self.logging_enabled = os.getenv('LOGGING_ENABLED', 'False').lower() in ('true', 't', '1')

    def is_logging_enabled(self):
        return self.logging_enabled

if __name__ == "__main__":
    flags = FeatureFlags()

    if flags.is_logging_enabled():
        print("Logging is enabled")
    else:
        print("Logging is disabled")

# Logging Setup

def setup_logger(name, log_file, level=logging.DEBUG):
    """To setup as many loggers as needed."""
    # Source: https://stackoverflow.com/questions/11232230/logging-to-two-files-with-different-settings 

    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(fmt='%(asctime)s :: %(name)s :: %(levelname)-8s :: %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

if flags.is_logging_enabled() == True:

    SB_pandas_modifier_error_logger = setup_logger("SB_pandas_modifier_error_logger", "SB_pandas_modifier_error_logger_list.log", logging.DEBUG)
    SB_pandas_modifier_error_logger.debug("File error logger file has been initiated for modifying StudioBookings data.")
    
else:
    print(f"Logging feature flag turned off. Review the .env file and set to true to enable logging.")

# For each excel file. 

column_header_names = ['blank_rows', 'date', 'class_booked', 'class_date', 'class_time', 'package_name', 'balance', 'balance_used', 'remaining_balance', 'transaction_type', 'modified_by']


def date_cleanup(date_string:str) -> str:
    """Takes date_string input of DD-MM-YYYY HH:MM:SS or D/M/YY H:MM:SS PM/AM and provides an output in the YYYY-MM-DD format. 
    The purpose of this function is to clean up the dates within the combined excel file. 
    Args:
        date_string (str): date as a string in one of the stated formats:
            [D/M/YY H:MM:SS PM/AM]
            [DD-MM-YYYY HH:MM:SS]
    Returns:
        str: YYYY-MM-DD
    """
    # Regex format to check if it is what is expected. 

    # first_expected_format accounts for the variability in the non-zero padded date observed. 
    first_expected_format = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s(AM|PM)$')

    # second_expected_format does not have the non-zero-padded variability. 
    second_expected_format = re.compile(r'^(\d{2})-(\d{2})-(\d{4}) (\d{2}):(\d{2}):(\d{2})$')
    
    try:
        if first_expected_format.match(date_string):
            match_first = first_expected_format.match(date_string)
            
            # Parse out the provided date_string. 
            day, month, year, hour, minute, second, period = match_first.groups()
            if len(year) == 2:
                year = '20' + year
            if second is None:
                second = '00'

            # Modify the parsed components and pad them with a zero to match the needed inputs for the datetime methods.     
            datetime_str_consistent = f"{int(day):02d}/{int(month):02d}/{year}  {int(hour):02d}:{minute}:{second} {period}"
            
            # Create a datetime object 
            datetime_obj = datetime.strptime(datetime_str_consistent, '%d/%m/%Y %H:%M:%S %p')
            
            # Convert the datetime object to a string in the desired format. 
            output_str = datetime_obj.strftime('%Y-%m-%d')
            return output_str
        
        elif second_expected_format.match(date_string):
            datetime_obj = datetime.strptime(date_string, '%d-%m-%Y %H:%M:%S')
            output_str = datetime_obj.strftime('%Y-%m-%d')
            return output_str
        
        else:
            print("Date doesn't match any of the expected formats.")
            SB_pandas_modifier_error_logger.info(f"{date_string} is not in a valid format.")
            return None
        
    except ValueError as e:
        print(f"Error parsing date: {e}")
        SB_pandas_modifier_error_logger.info(f"Error parsing date: {e}")
        return None


def transform_raw_file(file_path: str, save_path:str) -> csv:
    """Modifies .xls file and converts to a cleaner .csv.

    Args:
        file_path (str): file path for where the .xls file lives. 

    Returns:
        csv: .csv file. 
    """
    file = file_path

    # Open the file and turn it into a pandas Dataframe. 
    workbook = xlrd.open_workbook_xls(file, ignore_workbook_corruption=True)
    SB_pandas_modifier_error_logger.debug(f"Workbook in {file} has been successfully opened.")
    data = pd.read_excel(workbook, names=column_header_names)
    SB_pandas_modifier_error_logger.debug(f"Workbook in {file} has been successfully turned into a dataframe.")


    # Drop the blank column, aka column 0, or column A
    data.drop(
        columns=data.columns[0], 
        axis=1, 
        inplace=True
        )
    # Drop blank rows that come through in spaces. 
    data.drop(
        data.index[1:6],
        inplace = True
    )

    # Get the header from the file that contains the name of the account holder. Remove unnecessary words. 
    account_name_title = data['date'].values[0]
    account_name = account_name_title.split(" ")[0] + " " + account_name_title.split(" ")[1]

    # Remove the first row containing the title. 
    data.drop(
        data.index[0],
        inplace = True
    )

    # Append the name to a new column for later analysis. 
    data['account_owner'] = account_name

    # Create a cleaned up date column. 
    data['cleaned_date'] = data['date'].apply(lambda x: date_cleanup(x))


    # Save to .csv
    full_save_path = (save_path + '/' 'modified ' + account_name_title + '.csv')
    data.to_csv(full_save_path)
    SB_pandas_modifier_error_logger.info(f"File in {file_path} has been successfuly converted to .csv and saved to {full_save_path}")
    

def check_for_blank_file(file_path:str) -> bool:
    """Checks if the file contains any data. Returns True if the file is blank. 

    Args:
        file_path (str): path to the file to check, has to be xls. 

    Returns:
        bool: True if blank, False if it contains anything we want. 
    """
    workbook = xlrd.open_workbook_xls(file_path, ignore_workbook_corruption=True)
    data = pd.read_excel(workbook, names=column_header_names)
    row_count = len(data.index)

    # Files with less 7 rows do not have any data for attendance history and are thus considered 'blank'. These files only contain a name. 
    if row_count < 7:
        return True
    
    # Returns false to state that the file is NOT blank. 
    elif row_count >= 7:
        return False
    

# Get a list of the files in the directory

directory_path = os.getenv("DIR1")

blank_files = []


# Loop through the files in the specified directory and get their paths. Check if they're blank and if not, transform them with the specified function. 

def transform_file_directory(directory_path: str, applied_function: function) -> None:
    """Look at each file within the directory path and get each file's individual path if not blank. Apply a function to each file path. 
    Exports a .csv file to cwd with a list of the files it has found to be blank. 

    Args:
        directory_path (str): directory path

    Returns: None 
    """
    for file_name in listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        
        # Set your save path here or in .env file.
        save_path = os.path.abspath('/Users/save_folder/')
        try:
            if check_for_blank_file(file_path) == False:
                applied_function(file_path, save_path)
                SB_pandas_modifier_error_logger.debug(f"The {applied_function} has been applied to {file_path}.")
            else:
                blank_files.append(file_name)
        except xlrd.biffh.XLRDError as e:
            SB_pandas_modifier_error_logger.debug(f"An error has occurred attempting to open {file_name}.")
            continue
    # Save a .csv file with a list of the files that are blank. 
    with open('blank_files_list.csv', 'w', newline='') as myfile:
        writer = csv.writer(myfile)
        for val in blank_files:
            writer.writerow([val])
 
def combine_all_modified_csv_file(directory_path:str, save_path:str) -> None:
    """Combines all of the .csv files within a directory and saves them as a single file.

    Args:
        directory_path (str): Path for where the .csv files to be combined are stored. 
        save_path (str): Path for where the combined file will be saved. 
    """
    SB_pandas_modifier_error_logger.debug(f"Starting to attempt to combine all modified csv files in {directory_path}.")
    df_list = []
    for file_name in listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        try:
            df = pd.read_csv(file_path)
            df_list.append(df)
        except UnicodeDecodeError as e:
            SB_pandas_modifier_error_logger.debug(f"An error has occured with {file_path} and presenting error {e}.")
        except Exception as e:
            SB_pandas_modifier_error_logger.debug(f"An error has occurred, {e}.")
        
        large_df = pd.concat(df_list, ignore_index=True)
    save_path = os.path.abspath(save_path)
    large_df.to_csv(os.path.join(save_path,'combined_modified_files.csv'), index=False)


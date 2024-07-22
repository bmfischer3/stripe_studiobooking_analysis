import stripe
import pandas as pd
from datetime import datetime, timedelta
import json
from pprint import pprint
import os
import logging
import re

from dotenv import load_dotenv

# Import .ENV details

load_dotenv()

# Set to either "kahunas" or "studiobookings"
selected_platform = os.getenv("PLATFORM")
logging.info(f"The selected platform is {selected_platform}. Proceeding with reports from {selected_platform}.")

stripe.api_version = os.getenv("STRIPE_API_VERSION")


# One of these needs to return True
is_run_from_json_enabled = os.getenv("RUN_FROM_JSON_ENABLED")
is_run_from_live_API_enabled = os.getenv("RUN_FROM_LIVE_API_ENABLED")

if is_run_from_json_enabled == True:
    data_source_selection = "Local JSON"
elif is_run_from_live_API_enabled == True:
    data_source_selection = "Live API"
else:
    print("Check .env Feature Flag for data source selection.")
    logging.info("Feature flag for data source (JSON/API) is incorrect. Please check .env file.")

if selected_platform.lower().strip() == "kahunas":
    stripe.api_key = os.getenv("STRIPE_SECRET_API_KEY_KAHUNAS")
    platform_name = "KAHUNAS"
elif selected_platform.lower().strip() == "studiobookings":
    stripe.api_key = os.getenv("STRIPE_SECRET_API_KEY_STUDIO_BOOKINGS")
    platform_name = "STUDIO_BOOKINGS"
else: 
    platform_name = "Check API Key, contact support."

# Initialize the stripe client. 
client = stripe.StripeClient(stripe.api_key)

# Feature Flags

class FeatureFlags:
    def __init__(self):
        # May want to implement additional checks shown here: https://stackoverflow.com/questions/63116419/evaluate-boolean-environment-variable-in-python
        # Retrieves the .env variable if present, else returns False, lowercases all and verifies one of the strings is a true value. 
        self.get_both_business_reports_enabled = os.getenv('GET_BOTH_BUSINESS_REPORTS_ENABLED', 'False').lower() in ('true', 't', '1')
        self.export_any_all_files_enabled = os.getenv('EXPORT_ANY_ALL_FILES_ENABLED', 'False').lower() in ('true', 't', '1')
        self.logging_enabled = os.getenv('LOGGING_ENABLED', 'False').lower() in ('true', 't', '1')
            
    def is_get_both_business_reports_enabled(self):
        return self.get_both_business_reports_enabled
    
    def is_export_any_all_files_enabled(self):
        return self.export_any_all_files_enabled

    def is_logging_enabled(self):
        return self.logging_enabled

if __name__ == "__main__":
    flags = FeatureFlags()

    if flags.is_logging_enabled():
        print("Logging is enabled")
    else:
        print("Logging is disabled")

    if flags.is_get_both_business_reports_enabled():
        print("Report downloading for Kahunas and StudioBookings is enabled.")
    else:
        print("Reporting downloading for Kahunas and StudioBookings is disabled.")

    if flags.is_export_any_all_files_enabled():
        print("Exporting of files of any type within any function is enabled.")
    else:
        print("Exporting of files of any type within any function is disabled.")


## Main Functions ## 
# Export Weekly Report Information to XLSX File

def main_create_weekly_xlsx_report(start_date: int, end_date: int) -> None:
    """Creates a xlsx report showing new clients added and successful and failed charges for period provided. Reports out the previous period's numbers in addition. 
        Created to show 14 day periods at a time. 
    Args:
        start_date (int): YYYYMMDD
        end_date (int): YYYYMMDD

    Returns:
        None
    """

    logger.debug("Creating the weekly XLSX report function has started.")

    # Convert start and end date to datetime objects. 
    try:
        if is_valid_date(start_date) == True and is_valid_date(end_date) == True:
            logger.debug("Provided dates are valid and is_valid_date function returns True for both.")
            start_date_dt = datetime.strptime(str(start_date), '%Y%m%d')
            end_date_dt = datetime.strptime(str(end_date), '%Y%m%d')
            logger.debug(f"DateTime objects created for the provided integer arguments. Provided DT startdate is {start_date_dt}, DT enddate is {end_date_dt}")
    except:
        pass

    # Calculate the previous week's start and end date. 

    previous_start_date = start_date_dt - timedelta(days=14)
    previous_end_date = end_date_dt - timedelta(days=14)

    # Convert the DT objects back to ints. 

    previous_start_date_str = previous_start_date.strftime("%Y%m%d")
    previous_end_date_str = previous_end_date.strftime("%Y%m%d")


    # Run functions to get data. 
    current_period_new_clients = return_list_of_clients(start_date, end_date)
    previous_period_new_clients = return_list_of_clients(previous_start_date_str, previous_end_date_str)

    current_period_new_charges = return_list_of_charges(start_date, end_date)
    previous_period_new_charges = return_list_of_charges(previous_start_date_str, previous_end_date_str)

    # Create clients DataFrames
    df1 = pd.DataFrame(current_period_new_clients)
    df1.loc["count_totals"] = df1.count()
    df2 = pd.DataFrame(previous_period_new_clients)
    df2.loc["count_totals"] = df2.count()
    df3 = pd.DataFrame(current_period_new_charges)

    try:
        df3.loc["sum_totals"] = df3.sum()
    except TypeError as e:
        logger.debug(f"Error occurred with summing totals of df3. Data columns are not totaled if error occurs.  {e}")
    
    df4 = pd.DataFrame(previous_period_new_charges)
    try:
        df4.loc["sum_totals"] = df4.sum()
    except TypeError as e:
        logger.debug(f"Error occurred with summing totals of df4. Data columns are not totaled if error occurs.  {e}")    

    cur_date_for_file_name = str(start_date) + '_to_' + str(end_date)
    prev_date_for_file_name = previous_start_date_str + '_to_' + previous_end_date_str

    if flags.is_export_any_all_files_enabled():
        with pd.ExcelWriter((cur_date_for_file_name+'_'+platform_name+'_'+'weekly_report'+'.xlsx'), engine='xlsxwriter') as writer:
            df1.to_excel(writer, 
                        sheet_name=cur_date_for_file_name + 'ccl',
                        )
            df2.to_excel(writer,
                        sheet_name=prev_date_for_file_name + 'pcl',
                        )
            df3.to_excel(writer,
                        sheet_name=cur_date_for_file_name + 'cch',
                        )
            df4.to_excel(writer,
                        sheet_name=prev_date_for_file_name + 'pch',
                        )
    else:
        logger.info("Exporting of files of any type within any functions is disabled. Check feature flag.")

# Download all stripe reports to JSON format. 

def gather_stripe_reports(start_date: int, end_date: int) -> json:
    """Creates local JSON files for a list of customers, payment intents, and events that occurred within the provided date ranges, inclusive. 

    Args:
        start_date (int): YYYYMMDD
        end_date (int): YYYYMMDD, must be greater than the start date.  

    Returns:
        json: JSON file to cwd. 
    """

    # Get a list of all customer accounts. 
    customer_list = stripe.Customer.list(limit=100)
    full_customer_list = []
    
    # The below iterates through all the pages within the API to get all accounts. 
    for customer in customer_list.auto_paging_iter():
        full_customer_list.append(customer)
    with open(f"{start_date}-{end_date}_customer_list.json", "w") as write_file:
        json.dump(full_customer_list, write_file)


    # Get a list of the payment intents. 
    payment_intents = stripe.PaymentIntent.list()
    with open(f"{start_date}-{end_date}_payment_intents_list.json", "w") as write_file:
        json.dump(payment_intents, write_file)


    # Get a list of the events. 
    events = stripe.Event.list(limit = 100)
    with open(f"{start_date}-{end_date}_events_list.json", "w") as write_file:
        json.dump(events, write_file)
    

# Return information from Stripe via Search

def return_list_of_customer_ids(start_date: int = 20200101, end_date: int = 20241230) -> list:
    """Returns a list of customer IDs only. 

    Args:
        start_date (int, optional): start_date in YYYYMMDD format. Defaults to 20200101.
        end_date (int, optional): end_date in YYYYMMDD format. Defaults to 20241230.

    Returns:
        list: Returns a list with customer IDs. 
    """
    # Date range is left wide open to create a list of all customer ID's. Range can be narrowed to a recent window for greater specificity. 
    conv_start_date = int(convert_datetime_to_epoch_unix(start_date))
    conv_end_date = int(convert_datetime_to_epoch_unix(end_date))
    date_range_query = ("created<" + str(conv_end_date) + " AND " + "created>" + str(conv_start_date))
    customer_id_results= stripe.Customer.search(query=date_range_query)

    customer_id_list = []

    for customer in customer_id_results.auto_paging_iter():
        customer_id = customer.get("id")
        customer_id_list.append(customer_id)

    return customer_id_list

def return_list_of_customer_emails(start_date: int = 20200101, end_date: int = 20241230) -> list:
    """Returns a list of customer emails only. 

    Args:
        start_date (int, optional): start_date in YYYYMMDD format. Defaults to 20200101.
        end_date (int, optional): end_date in YYYYMMDD format. Defaults to 20241230.

    Returns:
        list: Returns a list with customer emails. 
    """
    # Date range is left wide open to create a list of all customer ID's. Range can be narrowed to a recent window for greater specificity. 
    conv_start_date = int(convert_datetime_to_epoch_unix(start_date))
    conv_end_date = int(convert_datetime_to_epoch_unix(end_date))
    
    # Creates a query to pass to stripe.
    date_range_query = ("created<" + str(conv_end_date) + " AND " + "created>" + str(conv_start_date))
    logging.debug(f"The query passed to stripe for customer email request is: {date_range_query}.")

    customer_email_results= stripe.Customer.search(query=date_range_query)

    customer_email_list = []

    for customer in customer_email_results.auto_paging_iter():
        customer_email = customer.get("email")
        customer_email_list.append(customer_email)

    return customer_email_list

def get_customer_email_data(start_date=20200101, end_date=20241230, email_list=None) -> list:
    """Performs a query on the specific email list requested. A custom list can be provided, else a list of emails captured between the provided dates will be fetched using the return_list_of_customer_emails function. 
        Custom date range should be provided if defaulting to calling upon teh return_list_of_customer_emails function.

    Args:
        start_date (int, optional): YYYYMMDD
        end_date (int, optional): YYYYMMDD
        email_list (list, optional): list

    Returns:
        list: _description_
    """
    # Per Stripe documentation, you can't use a customer_id. Must be another field. 
    if email_list == None:
        email_list = return_list_of_customer_emails(start_date, end_date)
    elif email_list != None:
        email_list = email_list

    customer_details_list = []
    for customer_email in email_list:
        query = ("email:" + "'" + customer_email + "'")
        search_result = stripe.Customer.search(query=query)
        indv_details = []
        for data in search_result:
            customer_id = data.get("id")
            customer_email = data.get("email")
            created_date = convert_epoch_unix_to_human_readable(data.get("created"))
            indv_details.append(customer_id)
            indv_details.append(customer_email)
            indv_details.append(created_date)
            customer_details_list.append(indv_details)   
    return customer_details_list

def return_payment_intents(start_date: int, end_date: int) -> list:
    """_summary_ Returns a list of dictionaries. Each dictionary is a payment intent made by a single customer. 

    Args:
        start_date (int): YYYYMMDD format
        end_date (int): YYYYMMDD format

    Returns:
        list: dictionary pertaining to a single payment intent object.
    """

    conv_start_date = int(convert_datetime_to_epoch_unix(start_date))
    conv_end_date = int(convert_datetime_to_epoch_unix(end_date))

    date_range_query = ("created<" + str(conv_end_date) + " AND " + "created>" + str(conv_start_date))
    payment_intent_results= stripe.PaymentIntent.search(query=date_range_query)
    pprint(payment_intent_results, indent=4)
    
    p_intent_dict_list = []

    for event in payment_intent_results["data"]:
        created_date = event.get("created")
        if conv_start_date <= created_date and conv_end_date >= created_date:
            cust_id = event.get("customer")
            email = event.get("email")
            description = event.get("description")
            amount_received = event.get("amount_received")
        if cust_id:
            created_human_readable = convert_epoch_unix_to_human_readable(created_date)
            p_intent_details = {
            'email': email,
            'description': description,
            'created' : created_date,
            'created_readable' : created_human_readable,
            'amount_received': convert_cents_to_dollars(amount_received),
            'platform': platform_name
            }

            p_intent_dict = {}
            p_intent_dict.update({
                'customer_id' : cust_id,
                'data': p_intent_details
            })
            p_intent_dict_list.append(p_intent_dict)

    pprint(p_intent_dict_list, indent=4)
    return p_intent_dict_list

def return_total_clients(start_date: int, end_date: int) -> int:
    """Returns the quantity of clients created within the specified period. 

    Args:
        start_date (int): YYYYMMDD start date of the period. 
        end_date (int): YYYYMMDD end date of the period. 

    Returns:
        int: quantity of accounts created within the period. Duplicates removed. Checks for duplicates by email address. 
    """
    customer_list = return_list_of_clients(start_date, end_date)
    return (len(customer_list))

def return_list_of_clients(start_date: int, end_date: int) -> list:
    """Returns a list of clients created within the specified period with date created, customer id, and a platform_name identification.. 

    Args:
        start_date (int): YYYYMMDD start date of the period. 
        end_date (int): YYYYMMDD end date of the period. 

    Returns:
        list: list of accounts created within the period. Duplicates removed. Checks for duplicates by email address. 
    """
    
    conv_start_date = int(convert_datetime_to_epoch_unix(start_date))
    conv_end_date = int(convert_datetime_to_epoch_unix(end_date))

    date_range_query = ("created<" + str(conv_end_date) + " AND " + "created>" + str(conv_start_date))
    customer_search_results = stripe.Customer.search(query=date_range_query)

    customer_list = []
    unique_email_list = []
    duplicate_accounts = []

    for customer in customer_search_results.auto_paging_iter():
        customer_id = customer.get("id")
        customer_email = customer.get("email")
        created_date = convert_epoch_unix_to_human_readable(customer.get("created"))
        customer_info = []
        if customer_email not in unique_email_list:
            unique_email_list.append(customer_email)
            customer_info.append(platform_name)
            customer_info.append(customer_id)
            customer_info.append(customer_email)
            customer_info.append(created_date)
            customer_list.append(customer_info)
        if customer_email in unique_email_list:
            duplicate_accounts.append(customer_email)
    return customer_list

def return_list_of_charges_by_customer(start_date: int, end_date: int, customer_id: str) -> list:
    """Returns a list of one or multiple dictionaries dependent on whether a customer_id is supplied. If a customer_id is not supplied, the function will capture
    all charge events within the specified start/end date windows. If a customer_id is supplied, it will return the charge events for that customer. 

    Args:
        start_date (int): YYYYMMDD
        end_date (int): YYYYMMDD
        customer_id (None): cus_123xyz

    Returns:
        list of dictionaries or a list with a single dictionary. 

        {   'customer_email: 'john.doe@gmail.com',
            'customer_id': 'cus_123abc',
            'successful_charges': [ (charge_id, timestamp, attempted_amount, collected_amount)],
            'failed_charges': [same as above, if any. If no failures, this k/v paire does not exist.]}
    """

    conv_start_date = int(convert_datetime_to_epoch_unix(start_date))
    conv_end_date = int(convert_datetime_to_epoch_unix(end_date))

    customer_charges_list = []
    customer_id_list = []

    if not customer_id:
        query = ("created<" + str(conv_end_date) + " AND " + "created>" + str(conv_start_date)) 
        charges_search_results= stripe.Charge.search(query=query, limit=100)

        # Creates a list to iterate through. 
        for charge_event in charges_search_results["data"]:
            customer_id = charge_event.get("customer")
            if customer_id not in customer_id_list:
                customer_id_list.append(customer_id)


        # Iterates through the customer ID list and takes that customer ID to look for instances in the query where charge events match the customer ID. 
        for cust_id in customer_id_list: 
            list_of_successful_tuples = []
            list_of_failed_tuples = []
            customer_charges = {}
            for charge_event in charges_search_results["data"]:
                if cust_id == charge_event.get("customer"):
                    customer_charges["customer_id"] = charge_event.get("customer")
                    customer_charges["customer_email"] = charge_event.get("receipt_email")
                    if charge_event.get("status"):
                        if charge_event.get("status") == "succeeded":
                            success_tuple_of_charge = (
                                    charge_event.get("id"),
                                    convert_epoch_unix_to_human_readable(charge_event.get("created")),
                                    convert_cents_to_dollars(charge_event.get("amount")),
                                    convert_cents_to_dollars(charge_event.get("amount_captured"))
                                )
                            list_of_successful_tuples.append(success_tuple_of_charge)
                            customer_charges["successful_charges"] = list_of_successful_tuples
                        if charge_event.get("status") == "failed":
                            fail_tuple_of_charge = (
                                charge_event.get("id"),
                                convert_epoch_unix_to_human_readable(charge_event.get("created")),
                                convert_cents_to_dollars(charge_event.get("amount")),
                                convert_cents_to_dollars(charge_event.get("amount_captured"))
                            )
                            list_of_failed_tuples.append(fail_tuple_of_charge)
                            customer_charges["failed_charges"] = list_of_failed_tuples
            customer_charges_list.append(customer_charges)
        return customer_charges_list


    else:
        query = ("created<" + str(conv_end_date) + " AND " + "created>" + str(conv_start_date) + " AND " + "customer:" + "'" + customer_id + "'")
        charges_search_results= stripe.Charge.search(query=query)
        customer_charges["customer_id"] = customer_id
        customer_charges["customer_email"] = charges_search_results["data"][0].get("receipt_email")
        customer_charges = {}
        list_of_successful_tuples = []
        list_of_failed_tuples = []
        for charge in charges_search_results["data"]:
            if charge.get("status") == "succeeded":
                tuple_of_charges = (
                    charge.get("id"),
                    convert_epoch_unix_to_human_readable(charge.get("created")),
                    convert_cents_to_dollars(charge.get("amount")),
                    convert_cents_to_dollars(charge.get("amount_captured"))
                )
                list_of_successful_tuples.append(tuple_of_charges)
            customer_charges["successful_charges"] = list_of_successful_tuples

            if charge.get("status") == "failed":
                tuple_of_charges = (
                    charge.get("id"),
                    convert_epoch_unix_to_human_readable(charge.get("created")),
                    convert_cents_to_dollars(charge.get("amount")),
                    convert_cents_to_dollars(charge.get("amount_captured"))
                )
                list_of_failed_tuples.append(tuple_of_charges)
            customer_charges["failed_charges"] = list_of_failed_tuples
        customer_charges_list.append(customer_charges)
        return customer_charges_list

def return_total_of_charges_list(start_date: int, end_date: int) -> float:
    """Returns a float value of the total charges for a list of customers 

    Args:
        start_date (int): _description_
        end_date (int): _description_

    Returns:
        float: _description_
    """
    payments_list = return_list_of_charges_by_customer(start_date, end_date)
    total_revenue = 0
    for charge in payments_list:
        if type(charge[5]) == float or int:
            total_revenue += charge[5]
    return total_revenue

def return_list_of_charges(start_date: int, end_date: int) -> list:
    """Retruns of list of charges that occurred between the provided dates. 

    Args:
        start_date (int): YYYYMMDD
        end_date (int): YYYYMMDD

    Returns:
        list: list
    """
    conv_start_date = int(convert_datetime_to_epoch_unix(start_date))
    conv_end_date = int(convert_datetime_to_epoch_unix(end_date))
    list_of_charges = []
    query = ("created<" + str(conv_end_date) + " AND " + "created>" + str(conv_start_date)) 
    charges_search_results= stripe.Charge.search(query=query, limit=100)

    for charge_event in charges_search_results["data"]:
        indv_charge_dict = {}
        charge_event.get("customer")
        indv_charge_dict["charge_id"] = charge_event.get("id")
        indv_charge_dict["status"] = charge_event.get("status")
        indv_charge_dict["charge_date"] = convert_epoch_unix_to_human_readable(charge_event.get("created"))
        indv_charge_dict["customer_id"] = charge_event.get("customer")
        indv_charge_dict["receipt_email"] = charge_event.get("receipt_email")
        indv_charge_dict["description"] = charge_event.get("description")
        indv_charge_dict["amount_captured"] = convert_cents_to_dollars(charge_event.get("amount_captured"))
        list_of_charges.append(indv_charge_dict)

    return list_of_charges

def return_list_of_expiring_subscriptions() -> list:
    """Returns a list of subscriptions with their expiration dates.  

    Returns:
        list: list
    """
    subscription_list = stripe.Subscription.list(limit=100)
    expiring_subscriptions = []
    for i in subscription_list.auto_paging_iter():  
        indv_sub_details = {}
        indv_sub_details["customer_id"] = i.get("customer")
        indv_sub_details["current_period_start"] = i.get("current_period_start")
        indv_sub_details["current_period_end"] = i.get("current_period_end")
        indv_sub_details["cancel_at"] = i.get("cancel_at")
        expiring_subscriptions.append(indv_sub_details)
    return expiring_subscriptions



# Functions to create readable data

def convert_cents_to_dollars(cents: int) -> float:
    """_summary_ Converts cents into a float value to represent dollars. 

    Args:
        cents (int): integer value representing cents. 100 cents would equal 1 dollar. 

    Returns:
        float: representing dollars, ex. 1.50 would mean one dollar and 50 cents. 
    """
    return cents/100

def convert_datetime_to_epoch_unix(human_date: int) -> datetime:
    """_summary_ Converts a human readable date in the "YYYYMMDD" format into an epoch date. 

    Args:
        human_date (int): _description_

    Returns:
        datetime: returns epoch date format
    """

    return datetime.strptime(str(human_date), "%Y%m%d").timestamp()

def convert_epoch_unix_to_human_readable(epoch_date: int) -> datetime:
    """_summary_ Converts an epoch date to a human readable format. 
    
    Args:
        epoch_date (_int_): epoch time
    
    returns: Datetime
    """

    return datetime.fromtimestamp(epoch_date).strftime('%Y-%m-%d %H:%M:%S')


# Validation Functions

def is_valid_date(date:int) -> bool:
    """Validates the date format and checks that it is within a reasonable range to collect date (+/- 100 years from today)

    Args:
        date (int): date as an integer, no delimeters.

    Returns:
        bool: True/False. True if matches YYYYMMDD format.
    """
    date_regex = re.compile(r'^\d{8}$')
    if not (date_regex.match(str(date))):
        return False
    
    try:
        date_obj = datetime.strptime(str(date), '%Y%m%d')
    except ValueError:
        return False
    
    current_date = datetime.now()
    window1 = current_date - timedelta(days=365.25 * 100)
    window2 = current_date + timedelta(days=365.25 * 100)
    return window1 <= date_obj <= window2


# Logging

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
    log_dir = os.getenv("LOGGING_DIR")
    logger = setup_logger("logger", f"{log_dir}logging.log", logging.DEBUG)
    logger.debug("Initial loogging file has been created.")

    file_error_logger = setup_logger("file_error_logger", f"{log_dir}file_error_log_list.log", logging.DEBUG)
    file_error_logger.debug("File error logger file has been initiated.")
    
else:
    print(f"Logging feature flag turned off. Review the .env file and set to true to enable logging.")
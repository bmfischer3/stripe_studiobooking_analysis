from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


# Import environment varibales for logging in

gym_name = str(os.getenv("SB_GYM_NAME"))
login_name = os.getenv("SB_USERNAME")
password = os.getenv("SB_PASSWORD")
login_url = os.getenv("SB_LOGIN_URL")
driver = webdriver.Chrome()




def create_num_list(num1:int, num2:int) -> list:
    """Define which members you would like to download data on. Member ID's appear to start at 1 and move incrementally by 1. 
        For example, if you have 735 members, num = 1, num2 = 735

    Args:
        num1 (int): starting member ID number
        num2 (int): ending member ID number

    Returns:
        list: list of numbers to iterate through.
    """
    if (num1 == num2):
        return num1
    else:
        num_list = []
        while num1 < num2+1:
            num_list.append(num1)
            num1 += 1
        return num_list

# Create the numbered list. 
num_list = create_num_list(1, 642)

url_list = []


# Create the URL strings to download each report. 

# https://studiobookingonline.com/[gym_name]/excelreport/member-creditreport/client_id/[client_id]/excelexport/true

for i in num_list:
    url_string="https://studiobookingonline.com/" + gym_name + "/excelreport/member-creditreport/client_id/" + str(i) + "/excelexport/true"
    url_list.append(url_string)

# Navigate through the login screen. 
wait = WebDriverWait(driver, 10)
driver.get(login_url)
driver.find_element(By.ID, "username").send_keys(login_name)
driver.find_element(By.ID, "password").send_keys(password)
driver.find_element(By.ID, "submit").click()
print("Logged in")


for url in url_list:
    # Selenium to go and access each web address. Upon accessing the web address the .csv file will automatically download to Chrome's default download location. 
    driver.get(url)
    driver.implicitly_wait(3)

driver.quit()



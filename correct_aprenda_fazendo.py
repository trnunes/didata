import undetected_chromedriver.v2 as uc
from time import sleep
import time
username = 'tnunes'
password ='m1l@b0t&lh0'

driver = uc.Chrome()

driver.delete_all_cookies()
driver.get("https://www.aprendafazendo.net/mydidata/login/")


sleep(2)


driver.find_element("id",'id_username').send_keys(username)
driver.find_element("id",'id_password').send_keys(password)

driver.find_element("xpath",'//input[@type="submit"]').click()
sleep(2)
driver.get('https://www.aprendafazendo.net/mydidata/topic_progress/71/Uu9CZGyMnJambPjenmanRH/')

els = driver.find_elements("xpath", '//i[contains(@class, "cloud")]/..')
els += driver.find_elements("xpath", '//i[contains(@class, "triangle")]/..')
links = [l.get_attribute("href") for l in els]
for l in links:
    driver.get("https://www.aprendafazendo.net/mydidata/get_corrections/" + l.split("/")[-1])
    # import pdb;pdb.set_trace()


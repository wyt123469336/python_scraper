
# coding: utf-8

# In[ ]:

import requests
import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from time import sleep  
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


# In[ ]:


from Crypto.Cipher import AES
import os

#my_key = os.urandom(BLOCK_SIZE) use to generate random AES key


#to encrypt user password
def AES_encryption(private_info,my_key):
    BLOCK_SIZE = 16
    padding = '{'
    pad = lambda s: s+(BLOCK_SIZE-len(s)%BLOCK_SIZE)*padding
    encrypting = lambda c, s: c.encrypt(pad(s))
    cipher = AES.new(my_key)
    encoded = encrypting(cipher,private_info)
    return encoded

#to decrypt user password
def AES_decryption(encoded_info,my_key):
    padding = '{'
    decrypting = lambda c, e: c.decrypt(e).decode('utf-8').rstrip(padding)
    cipher = AES.new(my_key)
    decoded = decrypting(cipher,encoded_info)
    return decoded


# In[ ]:


#to let user type in their username and password to log into sites
def get_credential():
    usr = input("Enter your username\n")
    psd = getpass.getpass('Password:\n')
    psd_entrypted = AES_encryption(psd,my_key)
    return [usr,psd_entrypted]


# In[ ]:


#scrape xfinity bills

def scrape_xfinity(auth):
    caps = DesiredCapabilities().FIREFOX
    # caps["pageLoadStrategy"] = "normal"  #  complete
    caps["pageLoadStrategy"] = "eager"  #  interactive
    # caps["pageLoadStrategy"] = "none"   #  undefined
    firefox_profile = webdriver.FirefoxProfile()

    # firefox_profile.set_preference('permissions.default.image', 2)
    # firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')

    firefox_path = r'/usr/local/share/geckodriver'

    browser = webdriver.Firefox(capabilities=caps, executable_path=firefox_path,firefox_profile=firefox_profile)
    browser.get("https://login.xfinity.com/login")
    username = browser.find_element_by_id("user")
    password = browser.find_element_by_id("passwd")
    

    username.send_keys(auth[0])
    password.send_keys(auth[1])
    browser.find_element_by_id("sign_in").click()
    sleep(3)
    homepage = browser.current_url
    if homepage == "https://login.xfinity.com/login":
        print('please provide correct username and password')
        browser.quit()
        return False #Wrong authentication
    timeout = 30
    try:
        my_account_btn = WebDriverWait(browser, 180).until(EC.visibility_of_element_located((By.XPATH, "//html/body/xc-header/div[2]/div[2]/ul[1]/li[4]/a")))
        my_account_page = my_account_btn.get_attribute('href')
        browser.get(my_account_page)

    except TimeoutException:
        print("Timed out waiting for page to load")
        browser.quit()


    try:
        billing_page = WebDriverWait(browser, timeout).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='page-header']/div/div/div[1]/nav/a[2]"))).click()
    except TimeoutException:
        billing_page = None
        print("Timed out waiting for page to load")
        #browser.quit()
    last_payment = dict()
    try:
        WebDriverWait(browser, timeout).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div/div/div/div/main/section[2]/div/div/div[2]/div[1]/div/div/div[2]/div[2]/div/div[2]/p")))
    except TimeoutException:
        print("Timed out waiting for page to load")
        #browser.quit()
    last_payment['amount'] = browser.find_element_by_xpath("/html/body/div[1]/div[2]/div/div/div/div/main/section[2]/div/div/div[4]/div/div[2]/div/div[3]/span").text
    last_payment['date'] = browser.find_element_by_xpath("/html/body/div[1]/div[2]/div/div/div/div/main/section[2]/div/div/div[4]/div/div[2]/div/div[1]/span/span[2]").text

    current_balance = dict()
    current_balance['amount'] = browser.find_element_by_xpath("/html/body/div[1]/div[2]/div/div/div/div/main/section[2]/div/div/div[2]/div[1]/div/div/div[2]/div[2]/div/div[2]/p").text
    if float(current_balance['amount'][1:]) == 0:
        current_balance['date'] = 'Come back tomorrow to check'
    else:
        current_balance['date'] = 'pseudo Next Date'
    print('your current balance:',current_balance['amount'])  
    print('your current due date:',current_balance['date'])
    print('your last payment:',last_payment['amount'])
    print('your last payment due date:',last_payment['date'])
    print('-------------------------------')
    try:
        WebDriverWait(browser, 3).until(EC.visibility_of_element_located((By.ID, "no"))).click()
    except TimeoutException:
        pass
    browser.find_element_by_xpath("/html/body/div[1]/div[2]/div/div/div/div/main/section[2]/div/div/div[2]/div[2]/div/div[2]/a/div[2]/span").click()
    past_statements_url = browser.current_url
    try:
        WebDriverWait(browser, 3).until(EC.visibility_of_element_located((By.ID, "no"))).click()
    except TimeoutException:
        pass

    latest_statements = browser.find_element_by_xpath("/html/body/div[1]/div[2]/div/div/div/div/main/section/div/div/div")
    my_keys = latest_statements.find_elements_by_class_name('card__content')
    values = latest_statements.find_elements_by_tag_name('a')
    print('Billing for the past 12 months\n')
    for i in range(min(12,len(my_keys))):
        print('Billing date:',my_keys[i].text)
        print('')
        past_year_bill(i,values,browser)
        print('-------------------------------')
    browser.quit()
    return True


# In[ ]:


#scrape barclays bills
def scrape_barclays(auth):   
    caps = DesiredCapabilities().FIREFOX
    # caps["pageLoadStrategy"] = "normal"  #  complete
    # caps["pageLoadStrategy"] = "eager"  #  interactive
    # caps["pageLoadStrategy"] = "none"   #  undefined

    firefox_profile = webdriver.FirefoxProfile()

    # firefox_profile.set_preference('permissions.default.image', 2)
    # firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')

    firefox_path = r'/usr/local/share/geckodriver'

    browser = webdriver.Firefox(capabilities=caps, executable_path=firefox_path,firefox_profile=firefox_profile)
    browser.get("https://www.barclaycardus.com/servicing/home?secureLogin")


    username = browser.find_element_by_id("username")
    password = browser.find_element_by_id("password")


    username.send_keys(auth[0])
    password.send_keys(auth[1])
    browser.find_element_by_id("loginButton").click()
    homepage = browser.current_url
    if homepage == "https://www.barclaycardus.com/servicing/authenticate":
        print('please provide correct username and password')
        browser.quit()
        return False #wrong authentication
    try:
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='viewStatement']"))).click()
    except TimeoutException:
        pass
    browser.switch_to_window(browser.window_handles[-1])
    try:
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[4]/div/div[1]")))
    except TimeoutException:
        pass
    save_most_recent_statement_pdf(browser,browser.current_url,'barclays')
    browser.close()
    browser.switch_to_window(browser.window_handles[0])
    current_balance = dict()
    current_balance['amount'] = browser.find_element_by_xpath("//*[@id='accountTile']/div[2]/div/div[2]/div[1]/div").text
    current_balance['date'] = browser.find_element_by_xpath("//*[@id='paymentTile']/div[2]/div/div[2]/div[1]/div/strong").text
    
    browser.find_element_by_xpath("//*[@id='b-primary-nav-links']/li[2]/a").click()
    browser.find_element_by_xpath("/html/body/section[2]/div[1]/nav/div/ul/li[2]/ul/li/div/div[2]/div/ul/li[3]/a").click()
    try:
        WebDriverWait(browser, 5).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "yui-dt12-col-payDate.yui-dt-col-payDate.yui-dt-sortable.yui-dt-desc")))
    except TimeoutException:
        pass
    past_payment_dates = browser.find_elements_by_class_name('yui-dt12-col-payDate.yui-dt-col-payDate.yui-dt-sortable.yui-dt-desc')[1:]
    past_payment_amount = browser.find_elements_by_class_name('yui-dt12-col-amount.yui-dt-col-amount.yui-dt-sortable')[1:]
    last_payment = dict()
    last_payment['amount'] = past_payment_amount[0].text
    last_payment['date'] = past_payment_dates[0].text

    print('your current balance:',current_balance['amount'])  
    print('your current due date:',current_balance['date'])
    print('your last payment:',last_payment['amount'])
    print('your last payment due date:',last_payment['date'])
    print('-------------------------------')

    day = current_balance['date'].split('.')[1]
    print('Payments for the past 12 months\n')
    for i in range(len(past_payment_dates)):
        print('Payment on',past_payment_dates[i].text+':',past_payment_amount[i].text)
        print('-------------------------------')
    browser.find_element_by_xpath("/html/body/section/div[1]/nav/div/ul/li[3]/a").click()
    browser.find_element_by_xpath("/html/body/section/div[1]/nav/div/ul/li[3]/ul/li/div/div[2]/ul/li[3]/a").click()
    try:
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/section/section/section/section[1]/section[2]/section/div/div/div[2]/div/ul/li[2]/a/em"))).click()
    except TimeoutException:
        print('timeout1')
    try:
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "yui-dt-data")))
    except TimeoutException:
        print('timeout2')
    past_balance = browser.find_elements_by_class_name('yui-dt-data')[-1].text.split('\n')
    past_balance_date = past_balance[-3::-3]
    past_balance_amount = past_balance[-2::-3]
    print('Billing for the past 12 months\n')
    for i in range(min(12,len(past_balance_date))):
        month, year = past_balance_date[i].split(' ')
        print('Date:', month+day+',',year)
        print('Amount:',past_balance_amount[i])
        print('-------------------------------')
    browser.quit()
    return True


# In[ ]:



     


# In[ ]:


# get bills from past year
def past_year_bill(i,values,browser):
    statement_url = values[i].get_attribute('href')
    if i == 0:
        save_most_recent_statement_pdf(browser,statement_url,'xfinity')
    #open tab
    browser.execute_script("""window.open("{}");""".format(statement_url))
    browser.switch_to_window(browser.window_handles[-1])

    scrape(i,browser)
    browser.close()
    browser.switch_to_window(browser.window_handles[0])


# In[ ]:


# perfrom scrape from poped up window (all past statements).
# since xfinity does not provide one table to display past bills
def scrape(i,browser):
    try:
        balance_amount = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[4]/div/div[1]/div[2]/div[{}]".format(29+i))))
        balance_due_date = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[4]/div/div[1]/div[2]/div[{}]".format(28+i))))
        payment_amount = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[4]/div/div[1]/div[2]/div[{}]".format(31+i))))
        payment_date = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[4]/div/div[1]/div[2]/div[{}]".format(33+i))))
    except TimeoutException:
        print('time out to get past bills')
        return
    print('balance_amount:',balance_amount.text)
    print(balance_due_date.text)
    print('Payment amount:',payment_amount.text)
    print(payment_date.text)


# In[ ]:


# use request module to save the most recent PDF
def save_most_recent_statement_pdf(browser,url,website):
    session = requests.Session()
    for cookie in browser.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    r = session.get(url, stream=True)
    chunk_size = 2000
    with open('statement_{}.pdf'.format(website), 'wb') as file:
        for chunk in r.iter_content(chunk_size):
            file.write(chunk)
    print('saved the most recent statement from {}'.format(website))


# In[ ]:


flag = True
print('Please select an account to view')
print("Type 'xfinity' or 'barclays' below")
print("Type 'forget' to clear saved authentication")
print("Type 'quit' to quit")
auth_xfinity = []
auth_barclays = []
while flag:
    print('=====================================================')
    userinput = input('please make a selection\n')
    if userinput == 'quit':
        flag = False
        print('Thanks for using')
    elif userinput == 'xfinity':
        # for first time login and after a failed login 
        if len(auth_xfinity) == 0:
            auth_xfinity = get_credential()
        #check if login successful or not
        logged = scrape_xfinity([auth_xfinity[0],AES_decryption(auth_xfinity[1],my_key)])
        if not logged:
            auth_xfinity = []
    elif userinput == 'barclays':
        # for first time login and after a failed login 
        if len(auth_barclays) == 0:
            auth_barclays = get_credential()
        #check if login successful or not
        logged = scrape_barclays([auth_barclays[0],AES_decryption(auth_barclays[1],my_key)])
        if not logged:
            auth_barclays = []
    elif userinput == 'forget':
        # to clear all saved credentials
        auth_xfinity = []
        auth_barclays = []
    else:
        print('\nplease make a valid selection')
        print("Type 'xfinity' or 'barclays' below")
        print("Type 'forget' to clear saved authentication")
        print("Type 'quit' to quit")


print("saved authentications")


print(auth_xfinity)


# In[ ]:


print(auth_barclays)


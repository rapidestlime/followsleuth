import logging

# Load selenium components
from seleniumwire import webdriver
#import seleniumwire.undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

import psycopg
from datetime import datetime
import requests
import time
import json
import brotli
import zstd

from dotenv import dotenv_values

# Load environment variables as a dictionary
env_vars = dotenv_values("secret.env")

DATABASE_URL = env_vars['database_url'] # used postgres application for easy setup


#-------- functions below mainly for telegram bot usage --------# 

def existing_chat(chat_id) -> bool:
    "Checks if current user is already registered"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(f"SELECT chat_id FROM users WHERE chat_id = {chat_id};")
    row = cur.fetchall()
    conn.close()

    return bool(row)

def register_chat(chat_id) -> bool:
    "Save new user into database"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    now_utc = datetime.utcnow()
    # Format the datetime object to a string
    timestamp_str = now_utc.strftime('%Y-%m-%d %H:%M:%S')
    try:
        cur.execute(f"INSERT INTO users (chat_id, date_subscribed) VALUES ({chat_id},'{timestamp_str}');")
        conn.commit()
        conn.close()
        return True
    except BaseException:
        logging.exception("An exception was thrown!")
        conn.rollback()
        conn.close()
        return False

def add_handles_to_db(user_input, chat_id) -> bool:
    "Save handles into database"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    handles = [line.strip() for line in user_input.splitlines() if line.strip()]
    placeholders = ', '.join(['%s'] * 2)
    rows = [(chat_id,handle.lower()) for handle in handles]
    try:
        cur.executemany(f"INSERT INTO handles (chat_id, handle_id) VALUES ({placeholders});",rows)
        conn.commit()
        conn.close()
        return True
    except BaseException:
        logging.exception("An exception was thrown!")
        conn.rollback()
        conn.close()
        return False

def remove_handles_from_db(user_input, chat_id) -> bool:
    "remove handles from database"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    handles = [line.strip() for line in user_input.splitlines() if line.strip()]
    rows = [(chat_id,handle.lower()) for handle in handles]
    try:
        cur.executemany(f"DELETE FROM handles WHERE chat_id = %s AND handle_id = %s;",rows)
        conn.commit()
        conn.close()
        return True
    except BaseException:
        logging.exception("An exception was thrown!")
        conn.rollback()
        conn.close()
        return False

def retrieve_handles_from_db(chat_id) -> bool:
    "gets current handles from database"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(f"SELECT handle_id FROM handles WHERE chat_id = {chat_id};")
    rows = cur.fetchall()
    conn.close()
    results = "\n".join([handle[0] for handle in rows])
    return results

def stop_tracking(chat_id) -> bool:
    "gets current handles from database"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    now_utc = datetime.utcnow()
    # Format the datetime object to a string
    timestamp_str = now_utc.strftime('%Y-%m-%d %H:%M:%S')
    try:
        cur.execute(f"UPDATE users SET date_end = '{timestamp_str}' WHERE chat_id = {chat_id};")
        conn.commit()
        conn.close()
        return True
    except BaseException:
        logging.exception("An exception was thrown!")
        conn.rollback()
        conn.close()
        return False

def resume_tracking(chat_id) -> bool:
    "gets current handles from database"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute(f"UPDATE users SET date_end = NULL WHERE chat_id = {chat_id};")
        conn.commit()
        conn.close()
        return True
    except BaseException:
        logging.exception("An exception was thrown!")
        conn.rollback()
        conn.close()
        return False

def self_destruct(chat_id) -> bool:
    "remove handles from database"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute(f"DELETE FROM handles WHERE chat_id = {chat_id};")
        conn.commit()
        cur.execute(f"DELETE FROM users WHERE chat_id = {chat_id};")
        conn.commit()
        conn.close()
        return True
    except BaseException:
        logging.exception("An exception was thrown!")
        conn.rollback()
        conn.close()
        return False

#-------- functions below mainly for scraper usage --------# 

# Webdriver Object Configurations
# Set up chrome driver
def driversetup():
    options = webdriver.ChromeOptions()
    #options = uc.ChromeOptions()
    
    # page load setting
    #options.page_load_strategy = "normal"  #  Waits for full page load
    #options.page_load_strategy = "eager"  #  Waits for page to be interactive
    options.page_load_strategy = "none"   # Do not wait for full page load
    
    # run Selenium in headless mode
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    
    # overcome limited resource problems
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("lang=en")
    
    # open Browser with set window size
    options.add_argument("--window-size=1920,1080")
    
    # disable infobars
    options.add_argument("disable-infobars")
    
    # avoid logging of info
    options.add_argument('--log-level=3')

    # disable extension
    options.add_argument("--disable-extensions")
    options.add_argument("--incognito")
    #options.add_argument('--ignore-certificate-errors-spki-list')
    options.add_argument("--disable-blink-features=AutomationControlled")
    #options.add_argument('--ignore-ssl-errors=yes')
    
    # add user agent
    options.add_argument('--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"')
    
    # executable path
    service = Service(executable_path='./chromedriver')
    driver = webdriver.Chrome(service=service, options=options,seleniumwire_options={'mitm_http2': False})
    
    return driver

def delete_unused_followings():
    "remove following records of handles no longer actively checked"
    sql = """
    DELETE FROM followings
    WHERE handle_id NOT IN (SELECT DISTINCT handle_id FROM handles);
    """
    try:
        conn = psycopg.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        conn.close()
        return True
    except BaseException:
        logging.exception("An exception was thrown for func: delete_unused_followings!")
        conn.rollback()
        conn.close()
        return False
    
def get_handles_list():
    "gets full list of handles to be active"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute("SELECT DISTINCT handle_id FROM handles;")
        rows = cur.fetchall()
        conn.close()
        return rows
    except BaseException:
        logging.exception("An exception was thrown!")
        conn.rollback()
        conn.close()

def login_actions(driver) -> None:
    "performs series of actions to log into X account"
    driver.get(url='https://www.x.com')

    login_button = WebDriverWait(driver, 60).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/login"]')))
    login_button.click()

    username_field = WebDriverWait(driver, 60).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="text"]')))
    username_field.send_keys(env_vars['twitter_username'])
    username_field.send_keys(Keys.ENTER)
    
    password_field = WebDriverWait(driver, 60).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
    password_field.send_keys(env_vars['twitter_password'])
    password_field.send_keys(Keys.ENTER)

def get_following_data(driver,handle_id):
    """check whether or not handle in tracking list is valid,
    if valid return data, else return None"""
    del driver.requests
    driver.get(url=f'https://www.x.com/{handle_id}/following')
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')))
    except:
        pass
    following_sub_url = 'Following?variables'
    following_user = []
    #following_name = []
    
    for request in driver.requests:
        if request and following_sub_url in request.url:
            #logging.info(eval(repr(request.response.headers))[11][1]) # debug encoding type
            try:
                decompress = brotli.decompress(request.response.body).decode() # zstd for non-headless, brotli for headless
            except:
                decompress = zstd.decompress(request.response.body).decode()
            else:
                logging.exception("An exception was thrown!")
                pass

            following_data = json.loads(decompress)
            try:
                for profile in following_data['data']['user']['result']['timeline']\
                                            ['timeline']['instructions'][3]['entries']:
                    following_user.append(f"{profile['content']['itemContent']['user_results']['result']['legacy']['screen_name']}")
                    #following_name.append(profile['content']['itemContent']['user_results']['result']['legacy']['name'])
            except:
                # take note there will be empty profile['content'] filler chunks by X.com to deter scraping
                logging.exception("An exception was thrown!")
                pass
        else:
            # edge cases where it is valid handle but no following data at all or non-existent handle
            pass
    
    return following_user


def invalid_handle_notif(handle_id) -> None:
    "sends push notification that handle no longer valid and removed"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(f"SELECT chat_id FROM handles WHERE handle_id = '{handle_id}';")
    rows = cur.fetchall()
    cur.execute(f"DELETE FROM handles WHERE handle_id = '{handle_id}';")
    conn.commit()
    conn.close()
    
    for e in rows:
        message = f"The handle you are tracking: {handle_id}, is no longer valid and removed!"
        url = f"https://api.telegram.org/bot{env_vars['bot_token']}/sendMessage?chat_id={e[0]}&text={message}"
        SentMessageResult = requests.get(url).json()
        if SentMessageResult['ok']:
            #SentMessageID = int(SentMessageResult['result']['message_id'])
            pass
        else:
            logging.info("Telegram Message was not sent.... UTC Time: ", str(datetime.utcnow()))
            #SentMessageID = 0

def get_existing_followings(handle_id):
    "retrieves exisiting following records for handle"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT following_id FROM followings WHERE handle_id = '{handle_id}';")
        rows = cur.fetchall()
        conn.close()
        return [e[0] for e in rows]
    except BaseException:
        logging.exception("An exception was thrown!")
        conn.rollback()
        conn.close()

def save_initial_followings(handle_id,followings_list) -> None:
    "dumps initial followings into database"
    now_utc = datetime.utcnow()
    # Format the datetime object to a string
    timestamp_str = now_utc.strftime('%Y-%m-%d %H:%M:%S')
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    placeholders = ', '.join(['%s'] * 3)
    rows = [(handle_id,following,timestamp_str) for following in followings_list]
    try:
        cur.executemany(f"INSERT INTO followings (handle_id, following_id, last_updated) VALUES ({placeholders});",rows)
        conn.commit()
        conn.close()
    except BaseException:
        logging.exception("An exception was thrown!")
        conn.rollback()
        conn.close()

def update_followings(handle_id,followings_list,existing_followings) -> None:
    "updates followings of specific handle in database"
    now_utc = datetime.utcnow()
    # Format the datetime object to a string
    timestamp_str = now_utc.strftime('%Y-%m-%d %H:%M:%S')
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    placeholders = ', '.join(['%s'] * 4)
    rows = []
    for following in followings_list:
        if following not in existing_followings:
            rows.append((handle_id, following, 'new', timestamp_str))
        else:
            rows.append((handle_id, following, None, timestamp_str))
    try:
        cur.execute(f"DELETE FROM followings WHERE handle_id = '{handle_id}';")
        conn.commit()
        cur.executemany(f"INSERT INTO followings (handle_id, following_id, status, last_updated) VALUES ({placeholders});",rows)
        conn.commit()
        conn.close()
    except BaseException:
        logging.exception("An exception was thrown!")
        conn.rollback()
        conn.close()


def send_following_notif() -> None:
    "sends push notification to users of new followings"
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(f"SELECT chat_id FROM users;")
    chat_id_list = [chat_id[0] for chat_id in cur.fetchall()]    
    
    for chat_id in chat_id_list:
        sql = f"""
        SELECT 
               b.handle_id,
               c.following_id
        FROM users a 
            INNER JOIN handles b ON a.chat_id = b.chat_id
            INNER JOIN followings c ON b.handle_id = c.handle_id
        WHERE c.status = 'new'
            AND a.date_end IS NULL
            AND a.chat_id = {chat_id}
        ORDER BY b.handle_id
        """
        cur.execute(sql)
        results = cur.fetchall()
        if results:
            message = "🆕 New Following Updates 🆕"
            handle_id_flag = None
            for row in results:
                if row[0] != handle_id_flag:
                    message += f"\n\n🧑 {row[0]}"
                else:
                    message += f"\n👉 www.x.com/{row[1]}"
            
            url = f"https://api.telegram.org/bot{env_vars['bot_token']}/sendMessage?chat_id={chat_id}&text={message}"
            SentMessageResult = requests.get(url).json()
            if SentMessageResult['ok']:
                #SentMessageID = int(SentMessageResult['result']['message_id'])
                pass
            else:
                logging.info("Telegram Message was not sent.... UTC Time: ", str(datetime.utcnow()))
                #SentMessageID = 0
    
    conn.close()

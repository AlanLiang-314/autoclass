from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import pytesseract
import time
from PIL import Image
import random
import re
import os
import platform
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from category2class import c2c

#====================================================================================================
## known issue: 
# the captcha recognition is not accurate, so you may need to try several times to login successfully
# the script may have bugs during non-enrollment periods

## Settings

# if True, the script will use the predefined curriculum, otherwise, the script will scrape the curriculum from the website
use_predifned_curriculum = True # currently unuseable
curriculum = [
    set([2, 3, 4, 5, 8, 9]), # Monday
    set(),  # Tuesday
    set([2, 3, 4, 5, 8, 9]),  # Wednesday
    set([2, 3, 4, 5]),  # Thursday
    set([12, 13, 14, 15]),  # Friday
    set(),  # Saturday
    set(),  # Sunday
]

# if True, the script will not show the conflicted courses
dont_show_conflicted = True

# course_list = set(["4103062_01"]) # the course list you want to add
course_list = set()


traverse_list = [
    # "通識-藝術與美學",
    # "通識-能源環境",
    # "通識-人文思維",
    # "通識-公民與社會參與",
    # "通識-經濟與國際脈動",
    # "通識-自然科學與技術",
    # "通識-中文",
    # "通識-英文",
    # "通識-資訊能力",
    # "通識-基礎概論",
    "軍訓",
    # "資工三",
    # "資工四",
    # "資工所一",
]

#====================================================================================================

def dummy_dotenv(path):
    dotenv_path = os.path.join(os.path.dirname(__file__), path) 
    env_var = {}
    with open(dotenv_path, 'r', encoding="utf-8") as f:
        key, value = f.readline().split('=')
        env_var[key] = value.strip('\n')
        key, value = f.readline().split('=')
        env_var[key] = value.strip('\n')

    return env_var

env_var = dummy_dotenv(".env")
username = env_var['USERNAME']
password = env_var['PASSWORD']

def get_url_builder(base_url, params):
    return base_url + '?' + ('&'.join([f"{key}={value}" for key, value in params.items()]))

edge_options = Options()
edge_options.use_chromium = True

system = platform.system()

if system == "Windows":
    edgedriver_path = 'edgedriver/msedgedriver.exe'
elif system == "Darwin":
    edgedriver_path = 'edgedriver/msedgedriver'
elif system == "Linux":
    edgedriver_path = 'edgedriver/msedgedriver'
else:
    raise OSError(f"Unsupported operating system: {system}")

service = Service(os.path.join(os.path.dirname(__file__), edgedriver_path))
driver = webdriver.Edge(service=service, options=edge_options)

driver.get('https://kiki.ccu.edu.tw/~ccmisp06/cgi-bin/class_new/login.php?m=0')

id_box = driver.find_element(By.CSS_SELECTOR, '#id')
password_box = driver.find_element(By.CSS_SELECTOR, '#password')

id_box.send_keys(username)
password_box.send_keys(password)

time.sleep(2)

# current we use pytesseract to recognize the captcha, but the accuracy is not good enough
# so we just try it until we get the correct captcha
is_login = False
for tries in range(10):
    print(f"Try {tries + 1}")
    image_element = driver.find_element(By.CSS_SELECTOR, '#captchaImage')

    image_element.screenshot('captcha.png')

    captcha_text = pytesseract.image_to_string(Image.open('captcha.png'))
    captcha_text = captcha_text.replace(" ", "")

    print("Captcha text:", captcha_text)

    captcha_box = driver.find_element(By.CSS_SELECTOR, '#captcha_input')
    captcha_box.clear()
    captcha_box.send_keys(captcha_text)
    submit_btn = driver.find_element(By.CSS_SELECTOR, '#submit_botton')
    time.sleep(1 + random.randint(0, 2))
    submit_btn.click()

    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
        print("Wrong captcha, try again.")
    except:
        print("Success login.")
        is_login = True
        break

if not is_login:
    print("Failed to login after 10 tries.")
    driver.quit()
    exit(1)

current_url = driver.current_url
# print("Current URL:", current_url)
params = re.findall(r'[?&]([^=#]+)=([^&#]*)', current_url)
for key, value in params:
    if key == "session_id":
        session_id = value


ch2num = {'一':1, '二':2, '三':3, '四':4, '五':5}
alphabet2num = {'A':[1, 2], 'B':[2, 3], 'C':[4, 5], 'D':[5, 6], 'E':[7, 8], 'F':[8, 9], 'G':[10, 11], 'H':[11, 12], 'I':[13, 14], 'J':[14, 15]}

def class_time_parser(class_time):
    temp = class_time.split(" ")
    flag = 0
    for t in temp:
        if flag == 1: break
        weekday = ch2num[t[0]] - 1
        
        class_time = t[1:].split(',')
        if all(ct.isdigit() for ct in class_time):
            class_time = list(map(int, class_time))
        else:
            class_time = []
            for ct in t[1:].split(','):
                if ct in alphabet2num:
                    class_time += alphabet2num[ct]
        
        for ct in class_time:
            if ct in curriculum[weekday]:
                flag = 1
                break
            
    return flag


def scrape_class_data(params):
    print("="*50)
    suceess_enroll_classes = []
    base_url = "https://kiki.ccu.edu.tw/~ccmisp06/cgi-bin/class_new/Add_Course01.cgi"
    target_url = get_url_builder(base_url, params)
    driver.get(target_url)

    element = driver.find_element(By.CSS_SELECTOR, 'body > center > form > table > tbody > tr:nth-child(3) > th:nth-child(2)')
    element_text = element.text

    match = re.search(r'第\d+/(\d+)頁', element_text)
    if match:
        total_pages = int(match.group(1))
        print("Total Pages:", total_pages)

    for i in range(total_pages):
        params['page'] = i + 1
        target_url = get_url_builder(base_url, params)
        driver.get(target_url)

        time.sleep(0.5 + random.randint(0, 2))

        table = driver.find_element(By.CSS_SELECTOR, 'body > center > form > table > tbody > tr:nth-child(1) > th > table > tbody')

        enroll_cnt = 0
        for i, row in enumerate(table.find_elements(By.TAG_NAME, 'tr')):
            if i == 0: continue
            
            info_list = []
            enrolled = False
            enrollable = False
            conflicted = 0
            class_id = None
            
            for j, cell in enumerate(row.find_elements(By.TAG_NAME, 'th')):                
                if j == 0:
                    try:
                        checkbox = cell.find_element("tag name", "input")
                        # checkbox.get_attribute("type") == "checkbox":
                        class_id = checkbox.get_attribute("value")
                        info_list.append("☐")
                    except:
                        info_list.append("☑")
                        enrolled = True
                
                if j in [1, 3]:
                    info_list.append(cell.text.replace("\n", " "))
                if j == 2:
                    info_list.append(cell.text.replace("\n", " "))
                    temp = cell.text.replace("\n", "")
                    if temp == "0":
                        enrollable = False
                    else:
                        enrollable = True
                
                if j == 8:
                    info_list.append(cell.text.replace("\n", " "))
                    temp = cell.text
                    conflicted = class_time_parser(temp)
                    if conflicted == 1 and not enrolled:
                        info_list.append("conflicted")
                        
            if (class_id in course_list) and enrollable and not enrolled:
                checkbox = row.find_elements(By.TAG_NAME, 'th')[0].find_element("tag name", "input")
                checkbox.click()
                enroll_cnt += 1
                suceess_enroll_classes.append((class_id, info_list[3]))
                info_list[0] = "☑"
            if dont_show_conflicted and conflicted and not enrolled:
                continue
            
            print(" | ".join(info_list))
        
        if enroll_cnt > 0:
            submit_btn = driver.find_element(By.CSS_SELECTOR, 'body > center > form > table > tbody > tr:nth-child(2) > th > input[type=submit]')
            submit_btn.click()
    
    return suceess_enroll_classes

# params = {
#     "session_id": session_id,
#     "use_cge_new_cate": 1,
#     "dept":"4106",
#     "grade":1,
#     "page":1,
#     # "cge_cate":2,
#     # "cge_subcate":1,
# }

for cate in traverse_list:
    params = c2c[cate]
    params["session_id"] = session_id
    classes = scrape_class_data(params)
    print(f"Successfully enrolled {len(classes)} classes in {cate}, they are: {classes}")

driver.quit()

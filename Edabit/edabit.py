from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import win32com.client
import time
import os
import csv

challenge_url = "https://edabit.com/challenges"

patience_time = 60

load_more_button = '//button[@class="ui fluid button"]'

driver = webdriver.Firefox()

driver.get(challenge_url)

# Open
driver.find_element_by_xpath('//div[@class="ui fluid selection dropdown"]').click()
driver.find_element_by_xpath('//div[@class="visible menu transition"]/div[@class="item"][5]').click()

# First HREF - get the rest after it loads
#driver.find_element_by_xpath('//div[@class="ui divided selection very relaxed middle aligned list"]/div[1]').click()

while True:
    try:
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        #time.sleep(6)
        element = WebDriverWait(driver, 150).until(
        EC.presence_of_element_located((By.XPATH, '//button[@class="ui fluid button"]'))
    )
        #time.sleep(6)
        loadMoreButton = driver.find_element_by_xpath('//button[@class="ui fluid button"]')
        
        loadMoreButton.click()
        time.sleep(10)
    except Exception as e:
        print(e)
        break
speaker = win32com.client.Dispatch("SAPI.SpVoice")
speaker.Speak("The loading process has finished!")
print('\a')

def create_directory(difficulty, name, examples, instruction_text, notes, exercise_url, codes, tests, solutions):
    os.chdir("D:\\work\\Scrapy Projects\\edabit selenium")
    try:
        if not os.path.exists(difficulty):
            os.makedirs(difficulty)
            print(f"Making directory: {difficulty}")
            os.chdir(difficulty)
            print(os.getcwd())
        else:
            os.chdir(difficulty)
        if os.path.exists(name):
            return f"Folder already exists: {name}"
        else:
            os.makedirs(f"./{name}" )
            print(f"Making a new directory: {name}")
            os.chdir(name)
            if '\n' in examples:
                examples = examples.split('\n')
                examples = [i for i in examples if i]
            with open(f"Instructions.csv", "w", encoding="utf-8") as inst:
                writer = csv.writer(inst)
        
                writer.writerow(["Instructions", "Examples", "Notes", "Exercise URL"])
                writer.writerow([instruction_text, examples, notes, exercise_url])

            with open("Code.py", "w") as code:
                for c in codes:
                    code.write(c + '\n')

            with open("Tests.py", "w") as test:
                for t in tests:
                    test.write(t + '\n')

            os.makedirs("./Solutions")
            os.chdir("Solutions")
            num = 1
            for sol in solutions:
                with open(f"Solution{num}.py", "w") as f:
                    f.write(sol)
                num += 1
    except OSError as e:
        print(e)
        print ("Error: Creating directory. " +  difficulty)

# Get all hrefs on page
hrefs = driver.find_elements_by_xpath('//div[@class="item no-highlight"]//a[@href]')
hrefs_list = []

# Append to list ( absolute urls )
for href in hrefs:
     hrefs_list.append(href.get_attribute("href"))

# Get all difficulties
all_difficulties = driver.find_elements_by_xpath('//div[@class="item no-highlight"]//a/div[3]')
difficulties = []
for diff in all_difficulties:
    difficulties.append(diff.text)

# Opens a new tab with the link, waits 10s, closes the tab leaving the main window intact
i = 0
for link in hrefs_list:
    
    # Get the difficulty
    difficulty = difficulties[i]

    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(link)
    time.sleep(10)
    
    # Name, tags
    element = WebDriverWait(driver, 150).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='ten wide column']//div[@class='rc-tabs-content rc-tabs-content-no-animated']//h2")))
    name = driver.find_element_by_xpath("//div[@class='ten wide column']//div[@class='rc-tabs-content rc-tabs-content-no-animated']//h2").text
    new_name = ""
    for char in name:
        if char.isalnum() or char.isspace():
            new_name += char
    if new_name:
        new_name = " ".join(new_name.split())
        name = new_name

    exercise_url = driver.current_url
    tags = []
    tags_elements = driver.find_elements_by_xpath("//div[@class='rc-tabs-tabpane rc-tabs-tabpane-active']//div[@class='sub header no-highlight'][2]/a")
    for elem in tags_elements:
        tags.append(elem.text)
    completed_tag = driver.find_elements_by_xpath("//div[@class='rc-tabs-tabpane rc-tabs-tabpane-active']//div[@class='sub header no-highlight'][2]/div")

    instruction_text = driver.find_element_by_xpath('//div[@class="rc-tabs-tabpane rc-tabs-tabpane-active"]//div[@class="grey-segment code-area instructions"]/div[2]/p').text
    examples = driver.find_element_by_xpath('//div[@class="rc-tabs-tabpane rc-tabs-tabpane-active"]//div[@class="grey-segment code-area instructions"]/div[2]/pre/code').text
    
    notes_elements = driver.find_elements_by_xpath('//div[@class="rc-tabs-tabpane rc-tabs-tabpane-active"]//div[@class="grey-segment code-area instructions"]/div[2]/ul/li')
    if not notes_elements:
        notes_elements = driver.find_elements_by_xpath('//div[@class="rc-tabs-tabpane rc-tabs-tabpane-active"]//div[@class="grey-segment code-area instructions"]/div[2]/p[3]')
    notes = []
    for note in notes_elements:
        notes.append(note.text)

    # Code tab
    code_tab = driver.find_element_by_xpath('//div[@class=" rc-tabs-tab"][1]').click()
    all_codes = driver.find_elements_by_xpath('//div[@class="rc-tabs-content rc-tabs-content-no-animated"]//div[@class="CodeMirror-code"]//pre')
    codes = []
    for code in all_codes:
        codes.append(code.text)

    # Solutions tab mechanics
    element = WebDriverWait(driver, 150).until(
        EC.visibility_of_element_located((By.XPATH, '//div[@class="rc-tabs-content rc-tabs-content-no-animated"]')))
    solutions_tab = driver.find_element_by_xpath('//div[@class="rc-tabs-nav rc-tabs-nav-animated"]/div[5]').click()
    
    # Avoid TimeoutException if solutions tab has already been unlocked
    if completed_tag:
        try:
            # Load the solutions
            element = WebDriverWait(driver, 100).until(
                EC.visibility_of_element_located((By.XPATH, '//div[@class="rc-tabs-content rc-tabs-content-no-animated"]/div[4]//div[@class="ui comments"]')))
            time.sleep(5)
        except TimeoutException as e:
            print(e)
    else:
        try:
            element = WebDriverWait(driver, 150).until(
                EC.presence_of_element_located((By.XPATH, '//h2[@class="ui grey icon header no-highlight"]/div[@class="sub header"]')))
            unlock_solutions = driver.find_element_by_xpath('//h2[@class="ui grey icon header no-highlight"]/div[@class="sub header"]').click()
            alert = driver.switch_to_alert()
            alert.accept()
            element = WebDriverWait(driver, 100).until(
                EC.visibility_of_element_located((By.XPATH, '//div[@class="rc-tabs-content rc-tabs-content-no-animated"]/div[4]//div[@class="ui comments"]')))
        except TimeoutException as e:
            print(e)
    

    all_solutions = driver.find_elements_by_xpath('//div[@class="solution-single"]/div[@class="ReactCodeMirror solution"]')
    solutions = []
    for sol in all_solutions:
        solutions.append(sol.text)
    
    # Tests
    tests_tab = driver.find_element_by_xpath('//div[@class="six wide column"]//div[@class=" rc-tabs-tab"]').click()
    element = WebDriverWait(driver, 150).until(
        EC.presence_of_element_located((By.XPATH, '//div[@class="CodeMirror-scroll"]')))
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@class="six wide column"]//div[@class="rc-tabs-content rc-tabs-content-no-animated"]//div[@class="CodeMirror-code"]/pre')))
    all_tests = driver.find_elements_by_xpath('//div[@class="six wide column"]/div[@class="rc-tabs rc-tabs-top"]//div[@id="Lab"]/div')
    
    all_tests = driver.find_elements_by_xpath('//div[@class="six wide column"]//div[@class="rc-tabs-content rc-tabs-content-no-animated"]//div[@class="CodeMirror-code"]/pre')
    tests = []
    for test in all_tests:
        inner_text = driver.execute_script("return arguments[0].innerText;", test)
        tests.append(test.text)

    create_directory(difficulty, name, examples, instruction_text, notes, exercise_url, codes, tests, solutions)

    i += 1

    time.sleep(10)
    driver.close()

    # Switch back to the first tab
    driver.switch_to.window(driver.window_handles[0])
speaker = win32com.client.Dispatch("SAPI.SpVoice")
speaker.Speak("The crawling process has finished!")
print('\a')
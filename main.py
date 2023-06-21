from selenium import webdriver
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import threading
import pandas
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import random
import requests
from pathlib import Path
import concurrent.futures

_POOL_SIZE = 1
_CSV_LOCATION = "./file.csv"
_TARGET_HOMEPAGE = "https://foerderportal.dosb.de/gutscheinaktion/sportvereinsscheck/"
_TEMP_MAIL_PROVIDER = "https://gecicimail.com.tr/"

_SAVE_DIRECTORY = r"xd/"
_ROW_NUMBER_TO_START_FROM = 0

try:
    Path(_SAVE_DIRECTORY).mkdir(exist_ok=True)
except: pass

_SPORTSLIST = [
    "Plakate",
    "Werbung im Fernsehen",
    "soziale Medien (Facebook, Instagram, TikTok, Twitter, LinkedIn…)",
    "Presse",
    "Internet-Seite / Newsletter des Deutschen Olympischen Sport-Bundes",
    "Internet-Seite / Newsletter eines Sport-Verbands oder Sport-Bundes",
    "Sport-Verein",
    "Stadt, Gemeinde, Landkreis",
    "Familie / Freunde",
    "Andere Vereins-Mitglieder",
    "Sonstiges (Zum Beispiel: Kranken-Kasse, Arzt / Ärztin)"
]

_GENDER_JS = """
function sln_genderizer(choice){
    var __genderCombobox = document.findElementById("undefinedgeschlecht");
    __genderCombobox.innerHTML = "<span class=\\"ui_select__value__label\\"><span class=\\"ui_select__value__label\\" title=\\"" +
                                 choice + "\\">" + choice + "</span></span>" +
                                 "<span class=\\"ui_select__caret\\" aria-hidden=\\"true\\"></span>";
}

function sln_listbox1(choice1, choice2, choice3){
    var __sportbox = document.findElementById("undefinedtreibensiemindestens1malinderwochesport");
    __sportbox.innerHTML = '<span class="ui_select__value__label"><span><span></span><span class=""><!----><span title="Ja, in einem Sport-Verein.">Ja, in einem Sport-Verein.</span></span></span><span><span>, </span><span class=""><!----><span title="Ja, privat. Zum Beispiel im Sport-Studio, Rad-Fahren, Joggen.">Ja, privat. Zum Beispiel im Sport-Studio, Rad-Fahren, Joggen.</span></span></span></span><!--v-if--><span class="ui_select__caret" aria-hidden="true"><i class="glyphicon glyphicon-chevron-down ui_select__caret__icon"></i></span>';

    var __sportschecksbox = document.findElementById("undefinedwiehabensievondensportvereinsscheckserfahren");
    __sportschecksbox.innerHTML = '<span class="ui_select__value__label"><span><span></span><span class=""><!----><span title="' + choice1 + '">'+ choice1 +'</span></span></span><span><span>, </span><span class=""><!----><span title="'+ choice2 +'">'+ choice2 +'</span></span></span><span><span>, </span><span class=""><!----><span title="'+choice3+'">'+choice3+'</span></span></span></span><!--v-if--><span class="ui_select__caret" aria-hidden="true"><i class="glyphicon glyphicon-chevron-down ui_select__caret__icon"></i></span>';
    
}
"""

def create_options(i, port=9200, temp="chromeDTemp"):
    datadir = str(Path(temp).absolute())
    chromeOption = webdriver.ChromeOptions()
    chromeOption.add_argument("--disable-web-security")
    chromeOption.add_argument("--user-data-dir=" + datadir + str(i))
    chromeOption.add_argument("--incognito")
    chromeOption.add_argument("--disable-gpu")
    chromeOption.add_argument("--remote-debugging-port=" + str(port + i))
    chromeOption.add_argument("start-maximized")
    chromeOption.add_argument('--no-sandbox')
    chromeOption.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    return chromeOption

global_locks = []
drivers = []
drivers_options = []
mail_drivers=[]
mail_drivers_options = []
for _ in range(_POOL_SIZE):
    global_locks.append(threading.Lock())

for i in range(_POOL_SIZE):
    drivers_options.append(create_options(i))
    
for i in range(_POOL_SIZE):
    mail_drivers_options.append(create_options(i, 9300, "chromeMDTemp"))

for i in range(_POOL_SIZE):
    # drivers.append(webdriver.Chrome(r"C:\Users\AZRA\Desktop\New folder\seleniumkeyfi\Browsers\chromedriver.exe", chrome_options=drivers_options[i]))
    drivers.append(webdriver.Chrome(options=drivers_options[i]))
    
for i in range(_POOL_SIZE):
    mail_drivers.append(webdriver.Chrome(options=mail_drivers_options[i]))
    
firstTime = True
def worker(row, row_id):
    with global_locks[row_id % _POOL_SIZE]:
        driver: webdriver.Chrome = drivers[row_id % _POOL_SIZE]
        mail_driver: webdriver.Chrome = mail_drivers[row_id % _POOL_SIZE]
        # Get temp mail and copy the mail address
        global firstTime
        if firstTime:
            mail_driver.get(_TEMP_MAIL_PROVIDER)
        
        time.sleep(0.5)
        
        mail_textbox = mail_driver.find_element(value='tempEmailAddress')
        if mail_textbox is None:
            print("OMG There is something wrong with mail_textbox variable!")
            return False
            
        _t0 = time.perf_counter()
        while mail_textbox.get_attribute('value').find("bekleyin...") != -1:
            _t1 = time.perf_counter()
            if _t1 - _t0 > 5:
                print("OMG mail textbox lasted for more than 5 seconds.")
                return False
        
        temp_mail = mail_textbox.get_attribute('value')
        if len(temp_mail) == 0:
            print("OMG There is something wrong with retrieved temp mail!")
            return False
        
        # if row_id < _POOL_SIZE:
        if firstTime:
            driver.get(_TARGET_HOMEPAGE)
            firstTime = False
        
        time.sleep(0.5)
        
        try:
            ele = WebDriverWait(driver, 10).until( #using explicit wait for 10 seconds
                EC.presence_of_element_located((By.ID, "undefinedemail")) #checking for the element with 'h2'as its CSS
            )
            # print("Page is loaded within 10 seconds.")
        except:
            print("Timeout Exception: Page did not load within 10 seconds.")
            return False
        
        # Type the email
        email_tbox = driver.find_element(value="undefinedemail")
        if email_tbox is None:
            print("OMG There is something wrong with email_tbox var")
            return False
        
        email_tbox.send_keys(temp_mail)
        
        # Type the first name
        firstname_tbox = driver.find_element(value='undefinedvorname')
        if firstname_tbox is None:
            print("OMG There is something wrong with firstname_tbox var")
            return False
        
        firstname_tbox.send_keys(row['Önisim = Vorname'])
        
        # Type the last name
        lastname_tbox = driver.find_element(value='undefinednachname')
        if lastname_tbox is None:
            print("OMG There is something wrong with lastname_tbox var")
            return False
        
        lastname_tbox.send_keys(row['Soyadi = Nachname'])
        
        gender = row['Cinsi M=Erkek / W = Bayan']
        
        # driver.execute_script(_GENDER_JS)
        # time.sleep(1)
        
        if gender == 'm':
            # target_gender = "Männlich"
            target_gender = "1"
        elif gender == 'w':
            # target_gender = "Weiblich"
            target_gender = "2"
        else:
            target_gender = "3"

        # driver.execute_script("sln_genderizer(arguments[0]);", target_gender)
        driver.execute_script("""
                              function sln_genderizer(choice){
                                  var __genderpopup = document.querySelector("#undefinedgeschlecht_list div div[role='group']").children[Number(choice)];
                                  __genderpopup.click();
                                  
    //var __genderCombobox = document.querySelector("#undefinedgeschlecht");
    //__genderCombobox.innerHTML = '<span class="ui_select__value__label"><!----><span class="ui_select__value__label" title="' + choice + '">'+choice+'</span></span><!--v-if--><!--v-if--><span class="ui_select__caret" aria-hidden="true"><i class="glyphicon glyphicon-chevron-down ui_select__caret__icon"></i></span>';
}
sln_genderizer(arguments[0]);""", target_gender)
        #Birth of date
        
        birth_tbox = driver.find_element(value='undefinedgeburtsjahr')
        if birth_tbox is None:
            print("OMG There is something wrong with birth_tbox var")
            return False
        
        bofd = row['Dontare Geburtsdatum']

        if bofd.find('.') != -1:
            target_bofd = bofd.split('.')[-1]
        else:
            target_bofd = str(random.randint(1960, 2000))
        
        birth_tbox.send_keys(target_bofd)
        
        # postcode
        
        post_tbox = driver.find_element(value='undefinedplz')
        if post_tbox is None:
            print("OMG There is something wrong with post_tbox var")
            return False
        
        postcode = str(int(row['PostaCodu = Postleitzahl (PLZ)']))
        post_tbox.send_keys(postcode)
        
        # listboxes
        selecteds = []
        
        while len(selecteds) < 3:
            random_item = random.choice(_SPORTSLIST)
            if random_item not in selecteds:
                selecteds.append(_SPORTSLIST.index(random_item))        
        
        driver.execute_script("""
                              function sln_listbox1(choice1, choice2, choice3){
                                  
                                  var __firstlistb = document.querySelector("#undefinedtreibensiemindestens1malinderwochesport_list div div[role='group']").children;
                                  __firstlistb[3].click();
                                  
                                  var __seclistb = document.querySelector("#undefinedwiehabensievondensportvereinsscheckserfahren_list div div[role='group']").children;
                                  __seclistb[Number(choice1)].click();
                                  __seclistb[Number(choice2)].click();
                                  __seclistb[Number(choice3)].click();
                                  
    //var __sportbox = document.querySelector("#undefinedtreibensiemindestens1malinderwochesport");
    //__sportbox.innerHTML = '<span class="ui_select__value__label"><span><span></span><span class=""><!----><span title="Ja, in einem Sport-Verein.">Ja, in einem Sport-Verein.</span></span></span><span><span>, </span><span class=""><!----><span title="Ja, privat. Zum Beispiel im Sport-Studio, Rad-Fahren, Joggen.">Ja, privat. Zum Beispiel im Sport-Studio, Rad-Fahren, Joggen.</span></span></span></span><!--v-if--><span class="ui_select__caret" aria-hidden="true"><i class="glyphicon glyphicon-chevron-down ui_select__caret__icon"></i></span>';

    //var __sportschecksbox = document.querySelector("#undefinedwiehabensievondensportvereinsscheckserfahren");
    //__sportschecksbox.innerHTML = '<span class="ui_select__value__label"><span><span></span><span class=""><!----><span title="' + choice1 + '">'+ choice1 +'</span></span></span><span><span>, </span><span class=""><!----><span title="'+ choice2 +'">'+ choice2 +'</span></span></span><span><span>, </span><span class=""><!----><span title="'+choice3+'">'+choice3+'</span></span></span></span><!--v-if--><span class="ui_select__caret" aria-hidden="true"><i class="glyphicon glyphicon-chevron-down ui_select__caret__icon"></i></span>';
    
}
sln_listbox1(arguments[0], arguments[1], arguments[2]);""", selecteds[0], selecteds[1], selecteds[2])
        
        # driver.execute_script("sln_listbox1(arguments[0], arguments[1], arguments[2]);", selecteds[0], selecteds[1], selecteds[2]) 
        
        # checkboxes
        
        wird_cbox = driver.find_element(By.CSS_SELECTOR, value='label[for="undefinednur1gutscheineinloesen"]')
        if wird_cbox is None:
            print("OMG There is something wrong with wird_cbox var")
            return False
        
        wird_cbox.click()
        
        werdenkann_cbox = driver.find_element(By.CSS_SELECTOR, value='label[for="undefinedkeinmitglied"]')
        if werdenkann_cbox is None:
            print("OMG There is something wrong with werdenkann_cbox var")
            return False
        
        werdenkann_cbox.click()
        
        genom_cbox = driver.find_element(By.CSS_SELECTOR, value='label[for="undefineddatenschutz"]')
        if genom_cbox is None:
            print("OMG There is something wrong with genom_cbox var")
            return False
        
        genom_cbox.click()
        
        # submit
        
        submit_button = driver.find_element(value='create_gutschein')
        if submit_button is None:
            print("OMG There is something wrong with submit_button var")
            return False
        
        submit_button.click()
        time.sleep(2.1)
        # mail_driver.refresh()
        # time.sleep(1.1)
        # driver.close()
        
        # continue with mail processing
        
        # mail_driver.refresh()
        
        
        retrieved_email = None
        while retrieved_email is None:
            try:
                retrieved_email = mail_driver.execute_script("return document.querySelector('#inboxTable tbody').children[0].children[0].textContent;")
                print("email: ", retrieved_email)
            except Exception as e:
                print(e)
            # mail_driver.refresh()
            if retrieved_email != "noreply@dosb.de":
                retrieved_email = None
                time.sleep(1)
                
        isital = False
        while isital is False:
            try:
                ret = mail_driver.execute_script("return document.querySelector('#inboxTable tbody tr.mail-open') !== undefined;")
            except:
                ret = None
            if ret is not None and ret:
                isital = True
            time.sleep(1)
        
        mail_driver.execute_script("document.querySelector('#inboxTable tbody tr.mail-open').click();")
        
        # sleep
        time.sleep(2.21)
        iframeText = mail_driver.execute_script('return document.querySelector("iframe").contentWindow.document.querySelector("body").innerText;')
        
        firstParag = iframeText.split("\n\n")[0]
        firstParagFirstSpaceLoc = firstParag.find(' ')
        fullname = firstParag[firstParagFirstSpaceLoc:-1]
        
        linkContainingParag = iframeText.split("\n\n")[2]
        linkContainingLastSpaceLoc = linkContainingParag.rfind(' ')
        link = linkContainingParag[linkContainingLastSpaceLoc:]
        
        response = requests.get(link)
        with open(str(Path(_SAVE_DIRECTORY, fullname + "@web.de.pdf")), "wb") as fhandle:
            fhandle.write(response.content)
        
        delete_btn = mail_driver.find_element(value="deleteEmailAddress")
        if delete_btn is None:
            print("OMG There is something wrong with delete_btn var")
            return False
        
        delete_btn.click()
        time.sleep(1.2)
        
        driver.refresh()
        # old_window_driver = driver.window_handles[0]
        # driver.execute_script("window.open('/gutscheinaktion/sportvereinsscheck/');")
        # driver.switch_to.window(old_window_driver)
        # driver.close()
        # driver.switch_to.default_content()
        
        mail_driver.delete_all_cookies()
        mail_driver.refresh()
        mail_driver.execute_script("document.location = '/';")
        # mail_driver.execute_script("window.open('/');")
        
        time.sleep(1.1)
        # drivers[row_id % _POOL_SIZE] = webdriver.Chrome(options=create_options(row_id % _POOL_SIZE))
        # mail_drivers[row_id % _POOL_SIZE] = webdriver.Chrome(options=create_options(row_id % _POOL_SIZE, 9100, "chromeMDTemp"))
        
        return True
        
        
    
df = pandas.read_csv(_CSV_LOCATION, sep=';', engine='python')

# Send rows to worker processes
rows = []
for index, row in df.iterrows():
    if index >= _ROW_NUMBER_TO_START_FROM:
        rows.append(row)
    
with ThreadPoolExecutor(_POOL_SIZE) as executor:
    row_ids = range(len(rows))
    future_to_url = {executor.submit(worker, row, row_id): row_id for row, row_id in zip(rows, row_ids)}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            data = future.result()
        except Exception as exc:
            print('%r generated an exception: %s' % (url, exc))
        else:
            print('%r page is %d bytes' % (url, len(data)))
    # executor.submit(worker, rows, row_ids)
    # for result in executor.map(worker, rows, row_ids):
    #     if result is False:
    #         print("Something's broken...")
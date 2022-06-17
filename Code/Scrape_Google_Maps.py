from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from sys import platform
from tqdm import tqdm
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import json
import getopt
import sys
import time
import random
import pandas as pd
import geopandas as gpd
from os.path import exists

def parse_relative_date(string_date):
    """Parse a relative data obtained from Google Maps reviews

    Args:
        string_date (str): The relative date, such as "Two weeks ago"

    Returns:
        datetime.datetime: Datetime object in YYYYMMDD
    """
    curr_date = datetime.now()
    split_date = string_date.split(' ')

    n = split_date[0]
    delta = split_date[1]

    if delta == 'year':
        return (curr_date - timedelta(days=365)).strftime('%Y-%m-%d')
    elif delta == 'years':
        return (curr_date - timedelta(days=365 * int(n))).strftime('%Y-%m-%d')
    elif delta == 'month':
        return (curr_date - timedelta(days=30)).strftime('%Y-%m-%d')
    elif delta == 'months':
        return (curr_date - timedelta(days=30 * int(n))).strftime('%Y-%m-%d')
    elif delta == 'week':
        return (curr_date - timedelta(weeks=1)).strftime('%Y-%m-%d')
    elif delta == 'weeks':
        return (curr_date - timedelta(weeks=int(n))).strftime('%Y-%m-%d')
    elif delta == 'day':
        return (curr_date - timedelta(days=1)).strftime('%Y-%m-%d')
    elif delta == 'days':
        return (curr_date - timedelta(days=int(n))).strftime('%Y-%m-%d')
    elif delta == 'hour':
        return (curr_date - timedelta(hours=1)).strftime('%Y-%m-%d')
    elif delta == 'hours':
        return (curr_date - timedelta(hours=int(n))).strftime('%Y-%m-%d')
    elif delta == 'minute':
        return (curr_date - timedelta(minutes=1)).strftime('%Y-%m-%d')
    elif delta == 'minutes':
        return (curr_date - timedelta(minutes=int(n))).strftime('%Y-%m-%d')
    elif delta == 'moments':
        return (curr_date - timedelta(seconds=1)).strftime('%Y-%m-%d')


# Proxy: https://medium.com/ml-book/multiple-proxy-servers-in-selenium-web-driver-python-4e856136199d
#PROXY = proxies[0].get_address()
#webdriver.DesiredCapabilities.CHROME['proxy']={
#    "httpProxy":PROXY,
#    "ftpProxy":PROXY,
#    "sslProxy":PROXY,    
#    "proxyType":"MANUAL"    
#}

def openChromeDriver():
    # Open chromedriver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--log-level=3')
    if platform == "linux":
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome("./chromedriver.exe", chrome_options=chrome_options)
    return driver


# TO-DO: Feed in urls of stores to driver.get()
# Currently, it is based on a placename

# Function to get all reviewer names
def getReviewer(placename):
    """Get all reviewer names

    Args:
        placename (str): Keyword(s) to search in Google Maps
    """
    driver = openChromeDriver()
    driver.get("https://www.google.com/maps/")

    # Search for 'KEYWORDS' in Google Maps, and wait four seconds before loading. 
    # KEYWORDS must be detailed so that Google Maps show only one result.
    # (e.g., KEYWORD 7-Eleven will search for many places, but 7-Eleven Downtown Knoxville will only indicate one place)

    # Keyword(s) for search in Google Maps
    KEYWORDS = placename
    # Locate the CSS Element for the search box in Google Maps
    searchbox = driver.find_element_by_css_selector("input#searchboxinput")
    # Put the input keywords in the search box
    searchbox.send_keys(KEYWORDS)
    # Locate the search button
    searchbutton = driver.find_element_by_css_selector("button#searchbox-searchbutton")
    # Click on the search button to execute the search
    searchbutton.click()

    time.sleep(4)

    # Locate the button for all reviews, and wait four seconds before loading
    reviewbutton = driver.find_element_by_css_selector("button.gm2-button-alt.HHrUdb-v3pZbf")
    # The CSS element for a direct POI URL, not obtained from a traditional search,: .Yr7JMd-pane-content-ZYyEqf
    # Click on the button for all reviews to navigate to the URL with all reviews for the location
    reviewbutton.click()

    time.sleep(4)

    # Load all elements indicating each review, and scroll through all reviews until the end of the review list
    # `#` sign is for id; `.` sign is for class
    # siAUzd-neVct: siAUzd-neVct
    # Yr7JMd-pane: Yr7JMd-pane
    # Yr7JMd-pane-content-ZYyEqf: Yr7JMd-pane-content-ZYyEqf
    try:
        reviewElement = driver.find_elements_by_css_selector("#pane > div.Yr7JMd-pane > div.Yr7JMd-pane-content > div.Yr7JMd-pane-content-ZYyEqf > div.siAUzd-neVct > div.siAUzd-neVct.section-scrollbox > div.siAUzd-neVct")[3]
    except IndexError:
        reviewElement = driver.find_elements_by_css_selector("#pane > div.Yr7JMd-pane > div.Yr7JMd-pane-content > div.Yr7JMd-pane-content-ZYyEqf > div.siAUzd-neVct > div.siAUzd-neVct.section-scrollbox > div.siAUzd-neVct")[2]

    # Find all reviews with data-review-id
    # Store the last review as lastReview
    # Execute scrolling until the last review (lastReview) is reached
    # scrollIntoView is a JavaScript method to scroll the parent container
    previousLastReview=None
    while True:
        time.sleep(1.3)
        reviews = reviewElement.find_elements_by_xpath("//div[contains(@data-review-id, 'Ch')]")
        lastReview = reviews[-1]
        driver.execute_script('arguments[0].scrollIntoView(true);', lastReview)
        if previousLastReview != lastReview:
            previousLastReview = lastReview
        else:
            break

    # Print reviewers
    for c in reviews:
        reviewer = c.get_attribute("aria-label")
        if reviewer is not None:
            print(reviewer)

    driver.close()

def getReviewerIter(placeList, verbose):
    isPrintOnConsole = False
    isPrintSeleniumOper = False

    if verbose == '1':
        isPrintOnConsole = True
    elif verbose == '2':
        isPrintOnConsole = True
        isPrintSeleniumOper = True

    driver = openChromeDriver()
    driver.get("https://www.google.com/maps/")

    placeListFile = open("./"+placeList, "r", encoding='UTF-8')
    reviewerListFile = open("./reviewer.txt", "w")
    errorListFile = open("./errors.txt", "w")

    for place in tqdm(placeListFile.read().splitlines()):
        try:
            # Search for 'KEYWORDS' in google Maps, and waits for 4 seconds to load. 
            # KEYWORDS must be detailed : so that Google Maps show only one result.
            # (i.e KEYWORD 세븐일레븐 will search for every place, but 세븐일레븐 혜화점 will indicate only one place)
            if isPrintOnConsole is True:
                tqdm.write("["+place+"]")

            reviewerListFile.write("["+place+"]\n")

            searchbox = driver.find_element_by_css_selector("input#searchboxinput")
            searchbox.clear()
            searchbox.send_keys(place)

            searchbutton = driver.find_element_by_css_selector("button#searchbox-searchbutton")
            searchbutton.click()

            time.sleep(4)

            try:
                # Click All Reviews button, and waits for 4 seconds to load
                reviewbutton = driver.find_element_by_css_selector("button.gm2-button-alt.HHrUdb-v3pZbf")
                reviewbutton.click()
            except NoSuchElementException:
                if isPrintOnConsole is True:
                    tqdm.write("No Reviews.\n")

                reviewerListFile.write("No Reviews.\n\n")
                time.sleep(1)
                continue

            time.sleep(4)

            # Load all elements indicating each reviews, scroll reviews till the end of review list
            try:
                reviewElement = driver.find_elements_by_css_selector("#pane > div.Yr7JMd-pane > div.Yr7JMd-pane-content > div.Yr7JMd-pane-content-ZYyEqf > div.siAUzd-neVct > div.siAUzd-neVct.section-scrollbox > div.siAUzd-neVct")[3]
            except IndexError:
                reviewElement = driver.find_elements_by_css_selector("#pane > div.Yr7JMd-pane > div.Yr7JMd-pane-content > div.Yr7JMd-pane-content-ZYyEqf > div.siAUzd-neVct > div.siAUzd-neVct.section-scrollbox > div.siAUzd-neVct")[2]

            previousLastReview=None
            while True:
                time.sleep(1.3)
                reviews = reviewElement.find_elements_by_xpath("//div[contains(@data-review-id, 'Ch')]")
                lastReview = reviews[-1]
                driver.execute_script('arguments[0].scrollIntoView(true);', lastReview)
                if previousLastReview != lastReview:
                    previousLastReview = lastReview
                else:
                    break

            # Print reviewers
            for c in reviews:
                reviewer = c.get_attribute("aria-label")
                if reviewer is not None:
                    if isPrintOnConsole:
                        tqdm.write(reviewer)
                    reviewerListFile.write(reviewer+'\n')

            if isPrintOnConsole:
                tqdm.write('\n')
            reviewerListFile.write('\n')
            backbutton = driver.find_element_by_xpath("//button[@aria-label='Back']")
            backbutton.click()
            time.sleep(4)
        except Exception as e:
            if isPrintOnConsole:
                tqdm.write(place+" - Error occured : "+str(e))
            
            errorListFile.write("Error occured : "+str(e)+"\n")
            driver.close()
            driver = openChromeDriver()
            driver.get("https://www.google.com/maps/")
            time.sleep(2)

    driver.close()


def getPOI(file):
    # TO-DO: Need to account for lag/high latency when waiting for page to load
    with open(file, "r") as f:
        for address_or_url in f:

            # Start time tracker
            start = time.time()

            # Open text file where scraped reviews will be stored as a JSON
            #reviewListFile = open("review_test2.txt", "w", encoding='UTF-8')
            # List where scraped POI information will be stored
            result = []
            # Data frame where all records will be stored
            df = pd.DataFrame(columns=['Name', 'Rating', 'Price', 'Type', 'Address', 'Hours', 'Website', 'Phone', 'PlusCode', 'Descript', 'Services', 'G_MAP_URL', 'PopTimes'])
            # Initialize Chrome driver
            driver = openChromeDriver()
            
            # If the input is a URL
            if "www.google.com/maps" in address_or_url:
            # Open the URL to a POI
                driver.get(address_or_url)
                # Wait five seconds for the page to load
                time.sleep(5)

            # Else it is assumed the input is the POI name + address
            else:
                # Open the URL to Google Maps
                driver.get("https://www.google.com/maps")
                # Wait five seconds for the page to load
                time.sleep(5)
                # Click on the Search box
                textBox = driver.find_element_by_xpath("//*[@id='searchboxinput']")
                textBox.click()
                # Input the POI location name and address into the search box
                textBox.send_keys(address_or_url)
                # Find the search button and click on it
                searchMaps = driver.find_element_by_xpath("//*[@id='searchbox-searchbutton']")
                searchMaps.click()
                time.sleep(5)

            # Get the URL of the page for the POI
            url = driver.current_url
            # Get the HTML of the webpage
            html = driver.page_source
            # Parse the html content
            soup = BeautifulSoup(html, "html.parser")

            # POI Name
            if driver.find_elements_by_class_name('x3AX1-LfntMc-header-title-title'):
                name = driver.find_element_by_class_name('x3AX1-LfntMc-header-title-title').text
            else:
                name = ""
            
            # Star Rating
            if driver.find_elements_by_class_name('aMPvhf-fI6EEc-KVuj8d'):
                rating = driver.find_element_by_class_name('aMPvhf-fI6EEc-KVuj8d').text
            else:
                rating = ""
            
            # Price
            if driver.find_elements_by_xpath("//span[contains(@aria-label, 'Price')]"):
                price = driver.find_element_by_xpath("//span[contains(@aria-label, 'Price')]").text
            else:
                price = ""
            
            # POI Type
            if driver.find_elements_by_xpath("//span[@class='h0ySl-wcwwM-E70qVe']/span[1]/button"):
                poi_type = driver.find_element_by_xpath("//span[@class='h0ySl-wcwwM-E70qVe']/span[1]/button").text
            else:
                poi_type = ""

            # Address
            if driver.find_elements_by_xpath("//button[@data-item-id='address']"):
                address = driver.find_element_by_xpath("//button[@data-item-id='address']").get_attribute('aria-label')
                address = address.strip("Address: ")
            else:
                address = ""
            
            # URL
            if driver.find_elements_by_xpath("//button[contains(@aria-label, 'Website')]"):
                website = driver.find_element_by_xpath("//button[contains(@aria-label, 'Website')]").get_attribute('aria-label')
            else:
                website = ""
            
            # Phone Number
            if driver.find_elements_by_xpath("//button[contains(@aria-label, 'Phone: (')]"):
                phone = driver.find_element_by_xpath("//button[contains(@aria-label, 'Phone: (')]").get_attribute('aria-label')
                phone = phone.strip("Phone: ")
            else:
                phone = ""

            # Google Maps PlusCode
            if driver.find_elements_by_xpath("//button[contains(@aria-label, 'Plus code')]"):
                pluscode = driver.find_element_by_xpath("//button[contains(@aria-label, 'Plus code')]").get_attribute('aria-label')
                pluscode = pluscode.strip("Plus code: ")
            else:
                pluscode = ""

            # Popular Times / Visitor Traffic
            # Inspiration from GitHub User - philshem; I had to modify class names and make some minor changes since their code was based on a version of Google Maps in early 2020
            # https://github.com/philshem/gmaps_popular_times_scraper/blob/master/scrape_gm.py
            # Set counters for the hour and day of the week & create a new list for data of popular times will be stored
            hour = ""
            day_of_week = 0
            day_times = []

            # Google Maps starts their weeks on Sunday
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

            if driver.find_elements_by_xpath("//div[@class='goog-inline-block goog-menu-button-caption']"):
                day = driver.find_element_by_xpath("//div[@class='goog-inline-block goog-menu-button-caption']").text

                # Check if the divs for popular times exist; if true, proceed; otherwise, skip this part
                if soup.find_all('div', {'class': 'O9Q0Ff-NmME3c-Utye1-ZMv3u'}):
                    # Find all divs representing the popular times for every hour in each day
                    pops = soup.find_all('div', {'class': 'O9Q0Ff-NmME3c-Utye1-ZMv3u'})
                    # For every div
                    for pop in pops:
                        # Store the aria-label for the div which is something like '35% busy at 11 AM.' into t
                        # The data is always stored beginning from Sunday regardless of location
                        #day_times.append(pop['aria-label'])
                        t = pop['aria-label']
                        hour_prev = hour
                        freq_now = None

                        try:
                            if 'Currently' not in t:
                                hour = t.split()[-2] + " " + t.split()[-1].replace('.', '')
                                freq = int(t.split()[0].replace('%', ''))
                            else:

                                # If a day is missing, the line(s) won't be parsable which can happen if the place is closed on that day
                                # Skip the missing days and hope it's only 1 day per line
                                # Increment the day counter
                                
                                # Grab the hour
                                hour = hour + 1
                                # Grab the popularity
                                freq = int(t.split()[0].replace('%', ''))

                                # Google Maps gives the current popularity, but only for the current hour
                                # If we're looking at the current hour, Google Maps has a different description
                                # Obtain the second to last element which is the typical popularity for the hour
                                try:
                                    freq_now = int(t.split()[-2])
                                except:
                                    freq_now = None
                            
                            if hour < hour_prev:
                                # Increment the day if the hour decreases
                                day_of_week += 1
                            
                            day_times.append([days[day_of_week % 7], hour, freq, freq_now])
                        
                        except:
                            # If a day is missing, the line(s) won't be parsable which can happen if the place is closed on that day
                            # Skip the day and hope it's only one day per line
                            # Increment the day counter
                            day_of_week += 1


            # Create a flag to differentiate between which if clause goes through so we can save a few seconds
            flag = True
            # The first if clause is for a webpage with opening hours as a dropdown
            # The elif clause is for a new webpage

            # Instantiate dictionary where the hours separated into opening and closing time will be stored
            hours = {}
            # Find the element that holds the opening hours
            # There are different HTML styles which means the class of the WebElement for opening hours varies
            if driver.find_elements_by_class_name('LJKBpe-open-R86cEd-LgbsSe-qwU8Me'):
                hoursButton = driver.find_element_by_class_name('LJKBpe-open-R86cEd-LgbsSe-qwU8Me')
                # Click on the element holding the opening hours to expand the box
                hoursButton.click()

                # Wait five seconds for the page to load
                time.sleep(5)

                # Get the HTML of the new webpage for opening hours
                html = driver.page_source
                # Parse the html content of the new webpage
                soup = BeautifulSoup(html, "html.parser")

                # Print the parsed HTML data for the opening hours table
                hours_table = soup.find('table', {'class':'y0skZc-jyrRxf-Tydcue NVpwyf-qJTHM-ibL1re'})
                # Locate the body of the table
                hours_table_body = hours_table.find('tbody')
                # Find all rows in the table
                hours_table_rows = hours_table_body.find_all('tr')
                # For every row in the table, which represents each day in the week and the corresponding opening hours
                hours_table_int = []
                for row in hours_table_rows:
                    # Find all cells in the row and store in cols
                    cols = row.find_all('td')
                    # For each element in each cell, retrieve the text, and then remove whitespaces
                    cols = [ele.text.strip() for ele in cols]
                    # In hours_table_int, store each day-hours pair
                    hours_table_int.append([ele.replace('Holiday hours Hours might differ', '').strip() for ele in cols if ele])

                # For each day-hours pair
                for dayhour in hours_table_int:
                    # Store the weekday/end into day
                    day = dayhour[0]
                    # Split the hours into opening and closing time
                    hr_startend = dayhour[1].split('–')       
                    # Create key:value pairs for each weekday/end and a list of the opening and closing time
                    hours[day] = hr_startend

            elif driver.find_elements_by_xpath("//button[contains(@aria-label, 'See more hours')]"):
                flag = False
                hoursButton = driver.find_element_by_xpath("//button[contains(@aria-label, 'See more hours')]")
                # Click on the element holding the opening hours to expand the box
                hoursButton.click()

                # Wait five seconds for the page to load
                time.sleep(5)

                # Get the HTML of the new webpage for opening hours
                html = driver.page_source
                # Parse the html content of the new webpage
                soup = BeautifulSoup(html, "html.parser")

                # Print the parsed HTML data for the opening hours table
                hours_table = soup.find('table', {'class':'y0skZc-jyrRxf-Tydcue NVpwyf-qJTHM-ibL1re'})
                # Locate the body of the table
                hours_table_body = hours_table.find('tbody')
                # Find all rows in the table
                hours_table_rows = hours_table_body.find_all('tr')
                # For every row in the table, which represents each day in the week and the corresponding opening hours
                hours_table_int = []
                for row in hours_table_rows:
                    # Find all cells in the row and store in cols
                    cols = row.find_all('td')
                    # For each element in each cell, retrieve the text, and then remove whitespaces
                    cols = [ele.text.strip() for ele in cols]
                    # In hours_table_int, store each day-hours pair
                    hours_table_int.append([ele.replace('Holiday hours Hours might differ', '').strip() for ele in cols if ele])

                # For each day-hours pair
                for dayhour in hours_table_int:
                    # Store the weekday/end into day
                    day = dayhour[0]
                    # Split the hours into opening and closing time
                    hr_startend = dayhour[1].split('–')       
                    # Create key:value pairs for each weekday/end and a list of the opening and closing time
                    hours[day] = hr_startend

            # If a new webpage for the opening hours was loaded
            if flag == False:
                # Go back to the main page
                driver.back()
                # Wait five seconds for the page to load
                time.sleep(5)

            # Instantiate a dictionary for service'/features details
            services = {}
            # Find the element that opens the POI service options, healthy and safety details, highlights, accessibility information, and accepted payments
            if driver.find_elements_by_class_name('uxOu9-sTGRBb'):
                detailsButton = driver.find_element_by_class_name('uxOu9-sTGRBb')
                # Click on the element holding the services and details to load the page
                detailsButton.click()

                # Wait five seconds for the page to load
                time.sleep(5)

                # POI Description
                if driver.find_elements_by_class_name('Y0mgC-text-ij8cu-text'):
                    description = driver.find_element_by_class_name('Y0mgC-text-ij8cu-text').text
                else:
                    description = ""

                # POI Service Features
                # Find all divs for each services/features subtype
                if driver.find_elements_by_class_name('LQjNnc-p83tee-JNdkSc'):
                    details_box = driver.find_elements_by_class_name('LQjNnc-p83tee-JNdkSc')

                    # For each subtype in the list of all subtypes
                    for subtype in details_box:
                        # Store the services/features subtype into detail_type to be used as a key for our dictionary later
                        services_type = subtype.get_attribute('aria-label')
                        services_list = []
                        # Find the unordered list and store into unorder
                        unorder = subtype.find_elements_by_class_name('LQjNnc-p83tee-JNdkSc-haAclf')
                        # For every unordered list (ul)
                        for cell in unorder:
                            # Find all listed elements (li) -- to clarify, these are different than lists in Python
                            cell_span = cell.find_elements_by_class_name('LQjNnc-p83tee-JNdkSc-ibnC6b')
                            # For all lists, find the service/feature description
                            for i in cell_span:
                                services_list.append(i.find_element_by_css_selector('span').get_attribute('aria-label'))
                        # Store the service type and list of service details as a key-value pair in the services dictionary 
                        services[services_type] = services_list

            else:
                description = ""

            # TO-DO: Geocode addresses into lat-lon
            
            # Append all scraped data to data-frame
            result = [[name, rating, price, poi_type, address, hours, website, phone, pluscode, description, services, url, day_times]]
            df = df.append(pd.DataFrame(result,
                            columns=['Name', 'Rating', 'Price', 'Type', 'Address', 'Hours', 'Website', 'Phone', 'PlusCode', 'Descript', 'Services', 'G_MAP_URL', 'PopTimes']),
                            ignore_index=True)
        
            # Geocode address using Nominatim
            # geo = geocode(result['address'], provider='nominatim', user_agent='gmapgeocode', timeout=5)
            # Join geocode result with nonspatial data for POIs
            # result_gdf = pd.join(geo, result)
            # Output file path
            # outfp = r"data/pois.shp"
            # Save to shapefile
            # result_gdf.to_file(outfp)

            # for c in reviews:
            #     counter1 += 0
            #     reviewer = c.get_attribute("aria-label")
            #     message = c.find_elements_by_css_selector("div.ODSEW-ShBeI-ShBeI-content > span")[1].get_attribute('innerHTML')
            #     rating = c.find_element_by_css_selector("span.ODSEW-ShBeI-H1e3jb").get_attribute('aria-label')[1:2]
            #     date = parse_relative_date(c.find_element_by_css_selector("span.ODSEW-ShBeI-RgZmSc-date").get_attribute('innerHTML'))
            #     if reviewer is not None:
            #         resultJSON.append({"name": reviewer, "date": date, "rating": rating, "review_message": message})
            #         counter2 += 0
            # print(counter1, counter2)

            # Dump all contents in resultJSON into a text document
            # result = {"result": result}
            # result = json.dumps(result, ensure_ascii=False)
        #    print(result)

            outcsv = "POIs.csv"
            # Check if CSV already exists
            # If it exists, append the scraped data for a POI to the CSV
            if exists(outcsv):
                df.to_csv(outcsv, mode='a', encoding='utf-8-sig', index=False, header=False)
            # Else, create a new CSV
            else:
                df.to_csv(outcsv, mode='w', encoding='utf-8-sig', index=False, header=True)

            # Close the driver
            driver.close()

            # End time tracker
            end = time.time()
            print("Elapsed time (secs): ", str(end-start))


    f.close()


def getReview(url):
    # Open text file where scraped information for reviews will be stored as a JSON
    reviewListFile = open("review_test_20220216.csv", "w", encoding='UTF-8')
    # List where dictionary records of reviews will be stored
    resultJSON = []
    # Initialize Chrome driver
    driver = openChromeDriver()
    # Open the URL to a POI
    driver.get(url)
    # Wait two seconds for the page to load
    time.sleep(2)

    # Locate the button for all reviews
    reviewbutton = driver.find_element_by_css_selector("button.gm2-button-alt.HHrUdb-v3pZbf")
    # The CSS element for a direct POI URL, not obtained from a traditional search,: .Yr7JMd-pane-content-ZYyEqf
    # Click on the button for all reviews to navigate to the URL with all reviews for the location
    reviewbutton.click()

    # Wait five seconds for the page to load
    time.sleep(5)

    # Load all elements indicating each review, scroll reviews till the end of review list
    # Find the element that holds all reviews
    try:
        reviewElement = driver.find_elements_by_css_selector("#pane > div.Yr7JMd-pane > div.Yr7JMd-pane-content > div.Yr7JMd-pane-content-ZYyEqf > div.siAUzd-neVct > div.siAUzd-neVct.section-scrollbox > div.siAUzd-neVct")[3]
    except IndexError:
        reviewElement = driver.find_elements_by_css_selector("#pane > div.Yr7JMd-pane > div.Yr7JMd-pane-content > div.Yr7JMd-pane-content-ZYyEqf > div.siAUzd-neVct > div.siAUzd-neVct.section-scrollbox > div.siAUzd-neVct")[2]

    # Execute scrolling to populate the node with actual reviews
    previousLastReview=None
    while True:
        # Generate a random number
        r = random.randint(30,90)
        # Set a random sleep time so that requests are not too fast nor bot-like
        time.sleep(r)
        # Find all reviews with data-review-id
        reviews = reviewElement.find_elements_by_xpath("//div[contains(@data-review-id, 'Ch')]")
        # Store the last review as lastReview
        lastReview = reviews[-1]
        # Scroll down the page; scrollIntoView is a JavaScript method to scroll the parent container (list of reviews)
        driver.execute_script('arguments[0].scrollIntoView(true);', lastReview)
        # Scroll until we reach the last review
        if previousLastReview != lastReview:
            previousLastReview = lastReview
        else:
            break
    
    # For every review, store the name, date, rating, and review text into a dictionary and store into resultJSON
    counter1 = 0
    counter2 = 0

    for c in reviews:
        counter1 += 0
        reviewer = c.get_attribute("aria-label")
        message = c.find_elements_by_css_selector("div.ODSEW-ShBeI-ShBeI-content > span")[1].get_attribute('innerHTML')
        rating = c.find_element_by_css_selector("span.ODSEW-ShBeI-H1e3jb").get_attribute('aria-label')[1:2]
        date = parse_relative_date(c.find_element_by_css_selector("span.ODSEW-ShBeI-RgZmSc-date").get_attribute('innerHTML'))
        if reviewer is not None:
            resultJSON.append({"name": reviewer, "date": date, "rating": rating, "review_message": message})
            counter2 += 0

    print(counter1, counter2)
    # Dump all contents in resultJSON into a text document
    resultJSON = {"result": resultJSON}
    resultJSON = json.dumps(resultJSON, ensure_ascii=False)
    print(resultJSON)
    reviewListFile.write(resultJSON)

    reviewListFile.close()
    driver.close()


def crawlhelp():
    print("\nScrape review information from Google Maps.\n")
    print("required arguments:")
    print("  -m [MODE], --mode [MODE]")
    print("      set mode of scraper. 5 strings are available.")
    print("        reviewer : get all reviewers from input string which indicates place")
    print("        reviewer_fromlist : get all reviewers from input file. file must be list of places you want to search for")
    print("        poi : get all pois from input string which indicates place")
    print("        review : get all reviews from input string which indicates place")
    print("        review_fromlist : get all reviews from input file. file must be list of places you want to search for\n")
    print("  -i [FILE or STRING], --input [FILE or STRING]")
    print("      input of scraper. must be string or filename.")
    print("      [reviewer, review] needs input as string, [reviewer_fromlist, review_fromlist] needs input as filename.")

def main(argv):
    INPUT = None
    EXECMODE = None
    VERBOSE = 0

    try:
        opts, args = getopt.getopt(argv[1:], "hm:i:v:", ["help", "mode=", "input=", "verbose="])
    except getopt.GetoptError:
        print("invalid arguments.")
        crawlhelp()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            crawlhelp()
        elif opt in ('-m', '--mode'):
            if arg is not None:
                EXECMODE = arg
            else:
                print('No mode specified. Must be one of [reviewer, reviewer_fromlist, review, review_fromlist]')
        elif opt in ('-i', '--input'):
            INPUT = arg
        elif opt == ('-v', '--verbose'):
            VERBOSE = arg
    
    if EXECMODE is None:
        print("Need -m or --mode.")
        crawlhelp()
        sys.exit(2)
    elif EXECMODE == "reviewer":
        if INPUT is None:
            print("need input as -i or --input.\nInput must be place name you want to search for.")
        else:
            getReviewer(INPUT)
    elif EXECMODE == 'reviewer_fromlist':
        if INPUT is None:
            print("need input as -i or --input.\nInput must be filename which contains list of place name you want to search for.")
        else:
            getReviewerIter(INPUT, VERBOSE)
    elif EXECMODE == "poi":
        if INPUT is None:
            print("need input as -i or --input. \nInput must be URL you want to search for.")
        else:
            getPOI(INPUT)
    elif EXECMODE == "review":
        if INPUT is None:
            print("need input as -i or --input.\nInput must be place name you want to search for.")
        else:
            getReview(INPUT)
    elif EXECMODE == "review_fromlist":
        print("Under construction...")
    else:
        print("["+EXECMODE+"] is invalid mode. Must be one of [reviewer, reviewer_fromlist, review, review_fromlist]")
        sys.exit(2)
    

if __name__ == "__main__":
    main(sys.argv)

#python mapscraper_test.py -m review -i https://www.google.com/maps/place/Trader+Joe's/@33.779751,-84.3683782,19z/data=!4m5!3m4!1s0x88f504161b143ad7:0xa4a7565c8e7d7f2f!8m2!3d33.7797175!4d-84.3679543
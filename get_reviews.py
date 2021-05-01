from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
import csv
import bs4
import re
import time
import random
import sys
import os
import requests

meta_names = ["for credit", "attendance", "would take again", "grade", "textbook", "online class"]
tag_names = ["gives good feedback", "respected", "lots of homework", "accessible outside class", "get ready to read", "participation matters", "skip class? you won't pass.", "inspirational",
                "graded by few things", "test heavy", "group projects", "clear grading criteria", "hilarious", "beware of pop quizzes", "amazing lectures", "lecture heavy", "caring",
                "extra credit", "so many papers", "tough grader"]
other_names = ["Professor Name", "Difficulty", "Quality", "School Name", 'pid', 'sid', 'Timestamp', 'Class']
os.environ['MOZ_HEADLESS'] = '1'

def get_html_soup(url, use_selenium=True):
    print(url)
    html_source = "foo"
    if use_selenium:
        driver = webdriver.Firefox()
        driver.get(url)
        accept_cookies_button = driver.find_element_by_xpath("/html/body//button[contains(@class, 'StyledCloseButton')]")
        accept_cookies_button.click()
        while(True):
            try:
                expand_button = driver.find_element_by_xpath("/html/body//button[contains(@class, 'PaginationButton')]")
                expand_button.click()
            except NoSuchElementException:
                break
            except StaleElementReferenceException:
                break
            except ElementClickInterceptedException:
                break
        html_source = driver.page_source
        driver.quit()
    else:
        time.sleep(random.randint(5, 10))
        r = requests.get(url)
        html_source = r.text

    return bs4.BeautifulSoup(html_source)

def get_school_link_list(soup):
    link_list = []
    for professor in soup.find_all(name='a', class_=re.compile("TeacherCard__StyledTeacherCard.*")):
        num_reviews = int(re.sub(' ratings$', '', professor.find(name='div', class_=re.compile("CardNumRating__CardNumRatingCount")).text))
        link_list.append(['https://www.ratemyprofessors.com' + professor['href'], num_reviews])
    return link_list

def get_ratings_dict(soup, sid, pid):
    professor_review_list = []
    professor_info = soup.find(name='div', class_=re.compile("TeacherInfo.*"))
    if professor_info is not None:
        professor_name_tags = professor_info.find(name='div', class_=re.compile("NameTitle__Name.*")).find_all(name="span")
        professor_school = professor_info.find(name='div', class_=re.compile("NameTitle__Title.*")).find(name="a").text
        professor_name = ""
        for name in professor_name_tags:
            if professor_name != "":
                professor_name += " "
            professor_name += name.text
        university = professor_info.find(name='div', class_=re.compile("NameTitle.*")).find(name="span").text
        for ratings_list in soup.find_all(name='ul', id='ratingsList'):
            for rating_list in ratings_list.find_all(name='li'):
                class_name = rating_list.find(name='div', class_=re.compile("RatingHeader__StyledClass.*"))
                if class_name is not None:
                    rating_dict = {}
                    rating_dict["Professor Name"] = professor_name
                    rating_dict["sid"] = sid
                    rating_dict["pid"] = pid
                    rating_dict["School Name"] = professor_school
                    online_image = class_name.find(name='img', class_=re.compile("OnlineCourseLogo.*"))
                    if online_image is None:
                        rating_dict['online class'] = False
                    else:
                        rating_dict['online class'] = True
                    rating_dict['Class'] = class_name.text
                    timestamp = rating_list.find(name='div', class_=re.compile("TimeStamp.*"))
                    rating_dict['Timestamp'] = timestamp.text
                    meta_items = rating_list.find_all(name='div', class_=re.compile("MetaItem.*"))
                    for meta_item in meta_items:
                        key_value = re.sub(':\s*$', '', meta_item.contents[0]).lower()
                        item_value = meta_item.find(name='span').contents[0].lower()
                        rating_dict[key_value] = item_value
                    tag_list = rating_list.find(name='div', class_=re.compile("RatingTags.*"))
                    if tag_list is not None:
                        for tag in tag_list.find_all(name='span'):
                            if tag.text.lower() in tag_names:
                                rating_dict[tag.text.lower()] = True
                    card_headers = rating_list.find_all(name='div', class_=re.compile("CardNumRating__CardNumRatingHeader.*"))
                    card_values = rating_list.find_all(name='div', class_=re.compile("CardNumRating__CardNumRatingNumber.*"))

                    rating_dict[card_headers[0].text] = card_values[0].text
                    rating_dict[card_headers[1].text] = card_values[1].text
                    for meta_name in meta_names:
                        if meta_name not in rating_dict:
                            rating_dict[meta_name] = None
                    for tag_name in tag_names:
                        if tag_name not in rating_dict:
                            rating_dict[tag_name] = False
                    professor_review_list.append(rating_dict)
    return professor_review_list

def create_ratings_csv(csv_path):
    last_professor_name = ""
    last_sid = 1
    with open(csv_path, 'r') as ratings_csv:
        csv_reader = csv.DictReader(ratings_csv)
        csv_list = list(csv_reader)
        last_prof = csv_list[-1]
        last_professor_name = last_prof["Professor Name"]
        last_sid = last_prof["sid"]
    with open(csv_path, 'a') as ratings_csv:
        fieldnames = []
        fieldnames += meta_names + tag_names + other_names
        csv_writer = csv.DictWriter(ratings_csv, fieldnames=fieldnames)
        sid = int(last_sid)
        reached_last_prof = False
        while True:
#            try:
                school_professor_list = get_school_link_list(get_html_soup('https://www.ratemyprofessors.com/search/teachers?query=*&sid=' + str(sid)))
                for professor_link in school_professor_list:
                    if reached_last_prof:
                        pid = professor_link[professor_link[0].find('=') + 1:]
                        review_list = []
                        if professor_link[1] > 20:
                            review_list = get_ratings_dict(get_html_soup(professor_link[0]), sid, pid)
                        else:
                            review_list = get_ratings_dict(get_html_soup(professor_link[0], False), sid, pid)
                        for review in review_list:
                            csv_writer.writerow(review)
                    if professor_link[0] == 'https://www.ratemyprofessors.com/ShowRatings.jsp?tid=850597':
                        reached_last_prof = True
                sid += 1
#            except:
#                print("Failed on school sid {}".format(sid))
#                print(sys.exc_info()[0])
#                break

create_ratings_csv('rmp_ratings.csv')

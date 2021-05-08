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
    # Get beautiful soup object containing html of url
    # url: url to get beautiful soup object from
    # use_selenium: whether selenium is requrired to click through all pagination

    html_source = "foo"
    if use_selenium:

        driver = webdriver.Firefox()
        driver.get(url)

        # click on button to accept cookies
        accept_cookies_button = driver.find_element_by_xpath("/html/body//div[contains(@class, 'FullPageModal__StyledFullPageModal')]/button[contains(@class, 'StyledCloseButton')]")
        accept_cookies_button.click()

        # repeatedly click on pagination button
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
        # use requests to get html if use_selenium is false

        time.sleep(random.randint(5, 10))
        r = requests.get(url)
        html_source = r.text

    return bs4.BeautifulSoup(html_source)

def get_school_link_list(soup):
    # get all professor review links from university search

    link_list = []
    for professor in soup.find_all(name='a', class_=re.compile("TeacherCard__StyledTeacherCard.*")):
        num_reviews = int(re.sub(' ratings$', '', professor.find(name='div', class_=re.compile("CardNumRating__CardNumRatingCount")).text))
        link_list.append(['https://www.ratemyprofessors.com' + professor['href'], num_reviews])
    return link_list

def get_ratings_dict(soup, sid, pid):
    # get all all review data from professor review page
    # soup: beautiful soup object with professor rating page html data
    # sid: rate my professor school id
    # pid: rate my professor professor id for page

    professor_review_list = []
    professor_info = soup.find(name='div', class_=re.compile("TeacherInfo.*"))
    if professor_info is not None:

        # Find professor name and university
        professor_name_tags = professor_info.find(name='div', class_=re.compile("NameTitle__Name.*")).find_all(name="span")
        professor_school = professor_info.find(name='div', class_=re.compile("NameTitle__Title.*")).find(name="a").text
        professor_name = ""
        for name in professor_name_tags:
            if professor_name != "":
                professor_name += " "
            professor_name += name.text
        university = professor_info.find(name='div', class_=re.compile("NameTitle.*")).find(name="span").text

        # Look through each rating
        for ratings_list in soup.find_all(name='ul', id='ratingsList'):
            for rating_list in ratings_list.find_all(name='li'):
                class_name = rating_list.find(name='div', class_=re.compile("RatingHeader__StyledClass.*"))
                if class_name is not None:
                    rating_dict = {}
                    rating_dict["Professor Name"] = professor_name
                    rating_dict["sid"] = sid
                    rating_dict["pid"] = pid
                    rating_dict["School Name"] = professor_school

                    # determine if the ratings is for an online course
                    online_image = class_name.find(name='img', class_=re.compile("OnlineCourseLogo.*"))
                    if online_image is None:
                        rating_dict['online class'] = False
                    else:
                        rating_dict['online class'] = True
                    rating_dict['Class'] = class_name.text

                    # Find date for rating
                    timestamp = rating_list.find(name='div', class_=re.compile("TimeStamp.*"))
                    rating_dict['Timestamp'] = timestamp.text
                    meta_items = rating_list.find_all(name='div', class_=re.compile("MetaItem.*"))

                    # Record value for all meta items
                    for meta_item in meta_items:
                        key_value = re.sub(':\s*$', '', meta_item.contents[0]).lower()
                        item_value = meta_item.find(name='span').contents[0].lower()
                        rating_dict[key_value] = item_value
                    tag_list = rating_list.find(name='div', class_=re.compile("RatingTags.*"))

                    # Record all tags listed in the review
                    if tag_list is not None:
                        for tag in tag_list.find_all(name='span'):
                            if tag.text.lower() in tag_names:
                                rating_dict[tag.text.lower()] = True
                    card_headers = rating_list.find_all(name='div', class_=re.compile("CardNumRating__CardNumRatingHeader.*"))
                    card_values = rating_list.find_all(name='div', class_=re.compile("CardNumRating__CardNumRatingNumber.*"))

                    rating_dict[card_headers[0].text] = card_values[0].text
                    rating_dict[card_headers[1].text] = card_values[1].text

                    # Fill in data for missing meta items and tags
                    for meta_name in meta_names:
                        if meta_name not in rating_dict:
                            rating_dict[meta_name] = None
                    for tag_name in tag_names:
                        if tag_name not in rating_dict:
                            rating_dict[tag_name] = False
                    professor_review_list.append(rating_dict)
    return professor_review_list

def create_ratings_csv(csv_path):
    # Cycle through professors in order of increasing sid
    # Output all reviews to csv on csv_path

    last_professor_name = ""
    last_sid = 1
    with open(csv_path, 'w') as ratings_csv:
        fieldnames = []
        fieldnames += meta_names + tag_names + other_names
        csv_writer = csv.DictWriter(ratings_csv, fieldnames=fieldnames)
        sid = int(last_sid)
        while True:
            school_professor_list = get_school_link_list(get_html_soup('https://www.ratemyprofessors.com/search/teachers?query=*&sid=' + str(sid)))
            for professor_link in school_professor_list:
                pid = professor_link[professor_link[0].find('=') + 1:]
                review_list = []
                if professor_link[1] > 20:
                    review_list = get_ratings_dict(get_html_soup(professor_link[0]), sid, pid)
                else:
                    review_list = get_ratings_dict(get_html_soup(professor_link[0], False), sid, pid)
                for review in review_list:
                    csv_writer.writerow(review)
            sid += 1

create_ratings_csv('rmp_ratings.csv')

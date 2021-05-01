import csv
import bs4
import re
import time
import random
import sys
import requests

column_names = ["overall_score", "name", "sid", "reputation", "location", "internet", "opportunity", 'clubs', 'happiness', 'food', 'social', 'safety', 'facilities']

def get_html_soup(url, use_selenium=True):
    print(url)
    time.sleep(random.randint(5, 10))
    r = requests.get(url)
    html_source = r.text
    return bs4.BeautifulSoup(html_source)

def get_ratings_dict(soup, sid):
    school_results = soup.find(name='div', class_="result-text")
    if school_results is not None:
        school_name = re.sub(r'^\W*', '', school_results.text)
        school_name = re.sub(r'\W*$', '', school_name)
        school_info = soup.find(name='div', class_="rating-breakdown")
        school_dict = {}
        if school_info is not None:
            overall_rating = school_info.find(name='div', class_='overall-rating')
            quality_ratings = school_info.find(name='div', class_='quality-breakdown')
            school_dict["name"] = school_name
            school_dict["sid"] = sid
            school_dict["overall_score"] = overall_rating.find(name='span', class_=re.compile('score.*')).text
            for rating_avg in quality_ratings.find_all(name='div', class_='rating'):
                school_dict[rating_avg.find(name='span', class_='label').text.lower()] = rating_avg.find(name='span', class_=re.compile('score.*')).text
        return school_dict

def create_ratings_csv(csv_path):
    with open(csv_path, 'w') as ratings_csv:
        csv_writer = csv.DictWriter(ratings_csv, fieldnames=column_names)
        sid = 1
        while True:
            school_scores = review_list = get_ratings_dict(get_html_soup('https://www.ratemyprofessors.com/campusRatings.jsp?sid=' + str(sid)), sid)
            if school_scores is not None:
                csv_writer.writerow(school_scores)
            sid += 1

create_ratings_csv('school_ratings.csv')

import csv
import re
import datetime

meta_names = ["for credit", "attendance", "would take again", "grade", "textbook", "online class"]
tag_names = ["gives good feedback", "respected", "lots of homework", "accessible outside class", "get ready to read", "participation matters", "skip class? you won't pass.", "inspirational",
                "graded by few things", "test heavy", "group projects", "clear grading criteria", "hilarious", "beware of pop quizzes", "amazing lectures", "lecture heavy", "caring",
                "extra credit", "so many papers", "tough grader"]
other_names = ["Professor Name", "Difficulty", "Quality", "School Name", 'pid', 'sid', 'Timestamp', 'Class']
grade_conversion = {'f': 0, 'd-': 1, 'd': 2, 'd+': 3, 'c-': 4, 'c': 5, 'c+': 6, 'b-': 7, 'b': 8, 'b+': 9, 'a-': 10, 'a': 11, 'a+': 12}
fieldnames = meta_names + tag_names + other_names

def clean_data(original_csv_name, updated_csv_name):
    # Put some review data into a more useful format

    ratings_list = []
    with open(original_csv_name, 'r') as ratings_csv:
        csv_reader = csv.DictReader(ratings_csv, fieldnames=fieldnames)
        for row in csv_reader:
            ratings_list.append(row)

    with open(updated_csv_name, 'w') as ratings_csv:
        csv_writer = csv.DictWriter(ratings_csv, fieldnames=fieldnames)
        for row in ratings_list:

            # Convert grade to number
            if row["grade"] in grade_conversion:
                row["grade"] = grade_conversion[row["grade"]]

            # Convert date to UNIX timestamp
            if row['Timestamp'] != 'Timestamp':
                string_date = re.sub(r' ([0-9])[a-z]*\,', r' 0\1', row['Timestamp'])
                string_date = re.sub(r'[a-z]*\,', '', string_date)
                date = datetime.datetime.strptime(string_date, '%b %d %Y')
                row["Timestamp"] = date.timestamp()

            # remove white space from professor name field
            row["Professor Name"] = re.sub(r'\W*$', '', row["Professor Name"])
            csv_writer.writerow(row)

clean_data('rmp_ratings.csv', 'cleaned_ratings.csv')

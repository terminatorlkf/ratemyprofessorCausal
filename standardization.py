import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import linear_model
from sklearn.utils import resample

model_attribute_names = ['online class', 'Timestamp', 'reputation', 'Quality']
COVID_start_timestamp = 1584247043
pd.options.mode.chained_assignment = None

def get_df_from_csv(csv_name):
    # get pandas dataframe from csv file
    return pd.read_csv(csv_name, quotechar='"', skipinitialspace=True)

def join_df_on_sid(student_rating_csv_name, university_rating_csv_name):
    # return joined student rating and university data

    student_rating_df = get_df_from_csv(student_rating_csv_name)
    university_rating_df = get_df_from_csv(university_rating_csv_name)
    return student_rating_df.merge(university_rating_df, on='sid')

def reduce_df_attributes(joined_df):
    # delete unused attributes from data

    return joined_df[model_attribute_names]

def convert_is_online(df):
    # Convert online class field from False or yes to 0 or 1

    df['online class'] = np.where(df['online class'], 1, 0)
    return df

def convert_timestamp_to_during_COVID(df):
    # Convert timestamp to boolean stating whether course was during COVID

    df['Timestamp'] = np.where(df['Timestamp'] < COVID_start_timestamp, 0, 1)
    df = df.rename(columns={'Timestamp': 'during COVID'})
    return df

def get_data_arr(student_rating_csv_name, university_rating_csv_name):
    # Call all functions required to do initial data conversion

    initial_df = join_df_on_sid('cleaned_ratings.csv', 'school_ratings.csv')
    converted_df = convert_timestamp_to_during_COVID(convert_is_online(reduce_df_attributes(initial_df)))
    return converted_df

def create_regression_model(ratings_df):
    # Create linear regression model for professor rating based on
    # whether the course was online and confounding variable

    modeling_df = ratings_df.copy(deep=True)
    return linear_model.LinearRegression().fit(modeling_df[['during COVID', 'reputation', 'reputation_squared',  'online class']], modeling_df[['Quality']])

def create_standardized_sample(ratings_df):
    # Create the new distribution after adjusting for confounders

    ratings_df['reputation_squared'] = pow(ratings_df['reputation'], 2)
    model = create_regression_model(ratings_df)
    block_2 = ratings_df.copy(deep=True)
    del block_2['Quality']
    block_3 = ratings_df.copy(deep=True)
    del block_3['Quality']

    # Set online class variable to 0 for all individuals in second table
    # and 1 for all individuals in second table
    block_2['online class'] = 0
    block_3['online class'] = 1

    # Fill in professor ratins with prediction from linear model
    block_2['Quality'] = model.predict(block_2)
    block_3['Quality'] = model.predict(block_3)

    del block_2['reputation_squared']
    del block_3['reputation_squared']
    return [block_2, block_3]

def calculate_effect_measures(block_2, block_3):
    # Calculate the causal effect measures
    # Block 2: sample where online class is set to 0 for all individuals
    # Block 3: sample where online class is set to 1 for all individuals

    online_average = block_3['Quality'].mean()
    offline_average = block_2['Quality'].mean()

    causal_difference = online_average - offline_average
    causal_ratio = online_average / offline_average

    return causal_difference, causal_ratio

def calc_bootstrap_confidence_interval(num_iterations, iteration_size, alpha=0.95):
    # Use bootstrap samples to calculate confidence intervals for
    # causal risk ratio and causal risk difference

    full_sample = get_data_arr('cleaned_ratings.csv', 'school_ratings.csv')
    if iteration_size is None:
        iteration_size = int(len(full_sample))
    difference_list = []
    ratio_list = []

    # Calculate causal risk difference and risk ratio in each sample
    for i in range(num_iterations):
        sample_1, sample_2 = create_standardized_sample(resample(full_sample, n_samples=iteration_size))
        causal_difference, causal_ratio = calculate_effect_measures(sample_1, sample_2)
        difference_list.append(causal_difference)
        ratio_list.append(causal_ratio)

    # Calculate confidence interval using normal approximation
    upper_p = ((1.0 - alpha) / 2.0) * 100
    lower_p = ((alpha + (1.0 - alpha)) / 2.0) * 100
    upper_confidence_difference = np.percentile(difference_list, upper_p)
    lower_confidence_difference = np.percentile(difference_list, lower_p)
    upper_confidence_ratio = np.percentile(ratio_list, upper_p)
    lower_confidence_ratio = np.percentile(ratio_list, lower_p)
    return lower_confidence_difference, upper_confidence_difference, lower_confidence_ratio, upper_confidence_ratio

lower_confidence_difference, upper_confidence_difference, lower_confidence_ratio, upper_confidence_ratio = calc_bootstrap_confidence_interval(1000, None)
print("Causal risk difference 95% confidence interval = [{}, {}]".format(lower_confidence_difference, upper_confidence_difference))
print("Causal risk ratio 95% confidence interval = [{}, {}]".format(lower_confidence_ratio, upper_confidence_ratio))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import linear_model
from sklearn.utils import resample

model_attribute_names = ['online class', 'Timestamp', 'reputation', 'Quality']
COVID_start_timestamp = 1584247043
pd.options.mode.chained_assignment = None

def get_df_from_csv(csv_name):
    return pd.read_csv(csv_name, quotechar='"', skipinitialspace=True)

def join_df_on_sid(student_rating_csv_name, university_rating_csv_name):
    student_rating_df = get_df_from_csv(student_rating_csv_name)
    university_rating_df = get_df_from_csv(university_rating_csv_name)
    return student_rating_df.merge(university_rating_df, on='sid')

def reduce_df_attributes(joined_df):
    return joined_df[model_attribute_names]

def convert_is_online(df):
    df['online class'] = np.where(df['online class'] == 'False', 0, 1)
    return df

def convert_timestamp_to_during_COVID(df):
    df['Timestamp'] = np.where(df['Timestamp'] < COVID_start_timestamp, 0, 1)
    df = df.rename(columns={'Timestamp': 'during COVID'})
    return df

def get_data_arr(student_rating_csv_name, university_rating_csv_name):
    initial_df = join_df_on_sid('cleaned_ratings.csv', 'school_ratings.csv')
    converted_df = convert_timestamp_to_during_COVID(convert_is_online(reduce_df_attributes(initial_df)))
    return converted_df

def create_regression_model(ratings_df):
    modeling_df = ratings_df.copy(deep=True)
    return linear_model.LinearRegression().fit(modeling_df[['during COVID', 'reputation', 'reputation_squared',  'online class']], modeling_df[['Quality']])

def create_standardized_sample(ratings_df):
    ratings_df['reputation_squared'] = pow(ratings_df['reputation'], 2)
    model = create_regression_model(ratings_df)
    block_2 = ratings_df.copy(deep=True)
    del block_2['Quality']
    block_3 = ratings_df.copy(deep=True)
    del block_3['Quality']

    block_2['online class'] = 0
    block_3['online class'] = 1

    block_2['Quality'] = model.predict(block_2)
    block_3['Quality'] = model.predict(block_3)

    del block_2['reputation_squared']
    del block_3['reputation_squared']
    return [block_2, block_3]

def calculate_effect_measures(block_2, block_3):

    online_average = block_3['Quality'].mean()
    offline_average = block_2['Quality'].mean()

    causal_difference = online_average - offline_average
    causal_ratio = online_average / offline_average

    return causal_difference, causal_ratio

def calc_bootstrap_confidence_interval(num_iterations, iteration_size, alpha=0.95):

    full_sample = get_data_arr('cleaned_ratings.csv', 'school_ratings.csv')
    if iteration_size is None:
        iteration_size = int(len(full_sample))
    difference_list = []
    ratio_list = []

    for i in range(num_iterations):
        sample_1, sample_2 = create_standardized_sample(resample(full_sample, n_samples=iteration_size))
        causal_difference, causal_ratio = calculate_effect_measures(sample_1, sample_2)
        difference_list.append(causal_difference)
        ratio_list.append(causal_ratio)

    upper_p = ((1.0 - alpha) / 2.0) * 100
    lower_p = ((alpha + (1.0 - alpha)) / 2.0) * 100
    upper_confidence_difference = np.percentile(difference_list, upper_p)
    lower_confidence_difference = np.percentile(difference_list, lower_p)
    upper_confidence_ratio = np.percentile(ratio_list, lower_p)
    lower_confidence_ratio = np.percentile(ratio_list, upper_p)
    return lower_confidence_difference, upper_confidence_difference, lower_confidence_ratio, upper_confidence_ratio

lower_confidence_difference, upper_confidence_difference, lower_confidence_ratio, upper_confidence_ratio = calc_bootstrap_confidence_interval(1000, None)
print("Causal risk difference 95% confidence interval = [{}, {}]".format(lower_confidence_difference, upper_confidence_difference))
print("Causal risk ratio 95% confidence interval = [{}, {}]".format(lower_confidence_ratio, upper_confidence_ratio))

#import necessary modules
import pandas as pd
#Requesting API data
import requests
import json

#Timezone management modules
import pytz
from datetime import datetime
from datetime import timedelta

#modules for plotting 
import seaborn as sns
import matplotlib.pyplot as plt

#First function obtaining data from API
def get_sunrise_sunset(lat, lng, date):
    """ 
    get sunrise sunset time for certain latitude and longitude at specific date.
    
    Args:
    lat: latitude
    lng: longitude
    date: date
    
    Returns: 
    result: result dictionary
    
    """   
    
    # API endpoint
    endpoint = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&date={date}"
    
    # get API response
    response = requests.get(endpoint)
    
    # Store and convert response into dictionary
    result = response.json()
    
    result['lat-lng'] = (lat, lng)
    result['date'] = date
    
    return result

# Assertion check for the get_sunrise_sunset function
sun_dict = get_sunrise_sunset(lat=42.3601, lng=-71.0589, date='2022-02-15')
sun_dict_expected = \
{'results': {'sunrise': '11:38:48 AM',
            'sunset': '10:17:50 PM',
            'solar_noon': '4:58:19 PM',
            'day_length': '10:39:02',
            'civil_twilight_begin': '11:11:30 AM',
            'civil_twilight_end': '10:45:08 PM',
            'nautical_twilight_begin': '10:38:37 AM',
            'nautical_twilight_end': '11:18:00 PM',
            'astronomical_twilight_begin': '10:06:05 AM',
            'astronomical_twilight_end': '11:50:33 PM'},
 'status': 'OK',
 'lat-lng': (42.3601, -71.0589),
 'date': '2022-02-15'}

assert sun_dict == sun_dict_expected, 'get_sunrise_sunset() error'

#TimeZone Considerations
def change_tz(dt, timezone_from, timezone_to):
    """ converts timezone of a timezone naive datetime object
    
    Args:
        dt (datetime): datetime (or time) object without timezone
        timezone_from (str): timezone of input
        timezone_to (str): timezone of output datetime
        
    Returns:
        dt (datetime): datetime object corresponding to 
            unix_time
    """
    
    dt_from = pytz.timezone(timezone_from).localize(dt)
    # Convert TimeZone
    dt = dt_from.astimezone(pytz.timezone(timezone_to))
    
    return dt

# Tests for timezone change function
# build test case 1 input / output
dt_no_tz = datetime(2021, 2, 13, 9, 54, 4, 270088)
dt_expect = datetime(2021, 2, 13, 14, 54, 4, 270088, tzinfo=pytz.timezone('GMT'))

# compute actual output
dt = change_tz(dt_no_tz, timezone_from='US/Eastern', timezone_to='GMT')

assert dt == dt_expect, 'change_tz() error'

# build test case 2 input / output
dt_no_tz = datetime(2021, 2, 13, 9, 54, 4, 270088)
dt_expect = datetime(2021, 2, 13, 9, 54, 4, 270088, tzinfo=pytz.timezone('GMT'))

# compute actual output
dt = change_tz(dt_no_tz, timezone_from='GMT', timezone_to='GMT')

assert dt == dt_expect, 'change_tz() error'

#Cleaning and series setting function
def clean_sun_dict(sun_dict, timezone_to):
    """ builds pandas series and cleans output of API
    
    Args:
        sun_dict (dict): dict of json (see ex below)
        timezone_to (str): timezone of outputs (API returns
            UTC times)
            
    Returns:
        sun_series (pd.Series): all times converted to
            time objects
    
    example sun_series:
    
    date            2021-02-13 00:00:00
    lat-lng        (36.72016, -4.42034)
    sunrise                    02:11:06
    sunrise_hr                    2.185
    sunset                     13:00:34
    sunset_hr                   13.0094
    dtype: object
    """
    
    results = sun_dict['results']
    sunrise_str = results['sunrise']
    sunset_str = results['sunset']
    date_str = sun_dict['date']
    
    # Convert from string to datetime
    sunrise_dt = pd.to_datetime(date_str + ' ' + sunrise_str)
    sunset_dt = pd.to_datetime(date_str + ' ' + sunset_str)
    
    # change timezone
    sunrise_local = change_tz(sunrise_dt, timezone_from='UTC', timezone_to=timezone_to)
    sunset_local = change_tz(sunset_dt, timezone_from='UTC', timezone_to=timezone_to)
    
    # Convert hours and minute values
    sunrise_hr = sunrise_local.hour + sunrise_local.minute / 60 + sunrise_local.second / 3600
    sunset_hr = sunset_local.hour + sunset_local.minute / 60 + sunset_local.second / 3600
    
    # Create series
    sun_series = pd.Series({
        'date': pd.to_datetime(date_str),
        'lat-lng': sun_dict['lat-lng'],
        'sunrise': sunrise_local.time(),
        'sunrise_hr': sunrise_hr,
        'sunset': sunset_local.time(),
        'sunset_hr': sunset_hr
    })
    
    return sun_series

#Assertion tests
sun_dict = {'results': {'sunrise': '11:38:48 AM',
                        'sunset': '10:17:50 PM',
                        'solar_noon': '4:58:19 PM',
                        'day_length': '10:39:02',
                        'civil_twilight_begin': '11:11:30 AM',
                        'civil_twilight_end': '10:45:08 PM',
                        'nautical_twilight_begin': '10:38:37 AM',
                        'nautical_twilight_end': '11:18:00 PM',
                        'astronomical_twilight_begin': '10:06:05 AM',
                        'astronomical_twilight_end': '11:50:33 PM'},
             'status': 'OK',
             'lat-lng': (42.3601, -71.0589),
             'date': '2022-02-15'}

# test without timezone conversion
sun_series = clean_sun_dict(sun_dict, timezone_to='GMT')

sun_series_exp = pd.Series(
{'date': datetime(year=2022, month=2, day=15),
'lat-lng': (42.3601, -71.0589),
'sunrise': time(hour=11, minute=38, second=48),
'sunrise_hr': 11.646666666666667,
'sunset': time(hour=22, minute=17, second=50),
'sunset_hr': 22.297222222222224})

assert sun_series.eq(sun_series_exp).all(), 'clean_sun_dict() error (GMT)'

# test with timezone conversion
sun_series = clean_sun_dict(sun_dict, timezone_to='US/Eastern',)

sun_series_exp = pd.Series(
{'date': datetime(year=2022, month=2, day=15),
'lat-lng': (42.3601, -71.0589),
'sunrise': time(hour=6, minute=38, second=48),
'sunrise_hr': 6.6466666666666665,
'sunset': time(hour=17, minute=17, second=50),
'sunset_hr': 17.297222222222224})

assert sun_series.eq(sun_series_exp).all(), 'clean_sun_dict() error (EST)'

#Integration to Dataframe 
def get_annual_sun_data(loc_dict, year=2021, period_day=30): 
    """ pulls evenly spaced sunrise / sunsets from API over year per city
    
    Args:
        loc_dict (dict): keys are cities, values are tuples of 
            (lat, lon, tz_str) where tz_str is a timezone
            string included in pytz.all_timezones
        year (int): year to query
        period_day (int): how many days between data queries
            (i.e. period_day=1 will get every day for the year)
            
    Returns:
        df_annual_sun (DataFrame): each row represents a 
            sunrise / sunset datapoint, see get_sunrise_sunset()
    """

    cycle_day = pd.to_datetime(f'{year}-01-01')
    cycle_city = loc_dict.keys()
    df_annual_sun = pd.DataFrame()
    #added a list
    data_list = []
    
    while cycle_day.year == year:
        for city in cycle_city:
            lat, lng, tz_str = loc_dict[city]
            city_series = pd.Series({'city': city})

            # get_sunrise_sunset
            sun_dict = get_sunrise_sunset(lat, lng, date=cycle_day.strftime('%Y-%m-%d'))
            # clean_sun_dict
            sun_series = clean_sun_dict(sun_dict, timezone_to=tz_str)

            # merge city_series and sun_series
            merged_series = pd.concat([city_series, sun_series])

            data_list.append(merged_series)

        cycle_day += timedelta(days=period_day)

    df_annual_sun = pd.DataFrame(data_list)
    return df_annual_sun

loc_dict = {'Boston': (42.3601, -71.0589, 'US/Eastern'),
            'Lusaka': (-15.3875, 28.3228, 'Africa/Lusaka'),
            'Sydney': (-33.8688, 151.2093, 'Australia/Sydney')}

df_annual_sun = get_annual_sun_data(loc_dict, year=2021, period_day=30)


#PLOTTING
sns.set(font_scale=1.2)

def plot_daylight(df_annual_sun):
    """ produces a plot of daylight seen across cities
    
    Args:
        df_annual_sun (DataFrame): each row represents a 
            sunrise / sunset datapoint, see get_sunrise_sunset()
    """
    
    # Convert the 'date' column to datetime format
    df_annual_sun['date'] = pd.to_datetime(df_annual_sun['date'])
    
    # Get the list of unique cities
    cities = df_annual_sun['city'].unique()
    
    plt.figure(figsize=(10, 6))
    
    # Plot the sunrise and sunset times for each city
    for city in cities:
        city_data = df_annual_sun[df_annual_sun['city'] == city]
        plt.fill_between(city_data['date'], city_data['sunrise_hr'], city_data['sunset_hr'], label=city)
        
    # Add title, labels, legend, and grid
    plt.title('Daylight at each location')
    plt.xlabel('Date')
    plt.ylabel('Local Millitary Time')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

#Visualization
df_annual_sun = get_annual_sun_data(loc_dict, year=2021, period_day=7)
plot_daylight(df_annual_sun)

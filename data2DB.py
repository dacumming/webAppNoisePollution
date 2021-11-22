# -*- coding: utf-8 -*-

# import modules
import requests
import pandas as pd
import json
import re
from sqlalchemy import create_engine
import numpy as np
import warnings
warnings.filterwarnings("ignore")
from pyproj import Proj, transform
from datetime import datetime as dt
from getColors import getColors

def getDataFromEpicollect(url = 'https://five.epicollect.net/api/export/entries/noise-pollution-survey?per_page=2000'):
    '''getDataFromEpicollect connects to Epicollect5 and returns a pandas 
    dataframe with data from Epicollect5 dataset'''
    
    # send the request to EpiCollect5
    response = requests.get(url)

    # store the response raw text in a variable
    raw_data = response.text

    # parse the raw text
    data = json.loads(raw_data)

    # tranform from JSON to pandas DataFrame
    df = pd.json_normalize(data['data']['entries'])

    #del response, raw_data, data
    return  df

def cleanNum(noise):
    ''''cleanNum deletes from a string any character that is not a number'''

    return re.sub('[^0-9.]', '', noise)

def LatLon2Mercator(lonlat):
    '''LatLon2Mercator converts tuple containing latitud & longitude
    to mercator x,y coordinates tuple'''

    return transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), lonlat[0], lonlat[1])

def strdate2ts(s):
    '''strdate2ts converts valid string format dates to POSIX timestamps
    Non-valid values are dropped'''
    try:
        return dt.timestamp(dt.strptime(s, '%d/%m/%Y'))
    except:
        return np.nan

def strtime2ts(s):
    '''strtime2ts converts string format daytimes to POSIX timestamps
    Non-valid values are dropped'''
    try:
        return dt.timestamp(dt.strptime(s, '%d/%m/%Y %H:%M:%S'))
    except:
        return np.nan

def dataPreprocessing(df):
    '''dataPreprocessing output the data ready to be stored in the DBMS '''

    # remove attributes that are not of interest for our project
    df.drop(columns=['ec5_uuid', 'created_at', 'uploaded_at', 'title', '1_Your_MIS_No',
                     '2_Your_subsector_1_t','6_Location_LatLong.accuracy',
                     '6_Location_LatLong.UTM_Zone'], inplace=True)

    # rename DataFrame columns
    df.rename(columns={'3_Date_of_entry_DDMM': 'dt', '4_Time_of_Entry': 't', '5_Major_Landuse_arou': 'landuse',
                       '7_Noise_Pollution_Le': 'enp', '8_Take_a_pic': 'pic', '6_Location_LatLong.latitude': 'lat',
                       '6_Location_LatLong.longitude': 'lon', '6_Location_LatLong.UTM_Northing': 'y',
                       '6_Location_LatLong.UTM_Easting': 'x'}, inplace=True)

    # convert ENP to numerical admissible values and discard not admissible ones
    df['enp'] = pd.to_numeric(df['enp'].apply(cleanNum), errors='coerce')
    df['enp'][df['enp'] > 100] = np.nan

    # processing of coordinates and conversion to mercator projection
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lonlat'] = df[['lon', 'lat']].apply(tuple, axis=1)
    df['xy'] = df['lonlat'].apply(LatLon2Mercator)
    aux = pd.DataFrame(df['xy'].tolist(), index=df.index)
    df['x'] = aux[0]
    df['y'] = aux[1]
    df.drop(columns=['lonlat', 'xy'], inplace=True)

    # time data processing: get POSIX timestamps for date and time
    df['dt_ts'] = df['dt'].apply(strdate2ts)
    aux = '02/01/1970 ' + df['t']
    df['t_ts'] = aux.apply(strtime2ts)

    #drop inadmissible values
    df.dropna(inplace=True)

    # get colors related to each noise pollution level
    df = getColors(df)

    return df


def importToPostgres(df):
    '''importToPostgres establishes a connection with PostgreSQL and import
    a DataFrame into PostgreSQL'''

    # create SQLAlchemy engine
    engine = create_engine('postgresql://postgres:password@localhost:5432/se4g')

    # import DataFrame to PostgreSQL database
    return df.to_sql('enp', engine, if_exists='replace', index=False)

# create pandas DataFrame with data downloaed from EpiCollect5
df = getDataFromEpicollect()

#data cleaning and preprocessing
df = dataPreprocessing(df)

# import DataFrame into a PostgreSQL table
importToPostgres(df)

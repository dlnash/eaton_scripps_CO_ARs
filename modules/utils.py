"""
Filename:    utils.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: utility functions
"""

import math

def roundPartial(value, resolution):
    return round(value / resolution) * resolution

def round_latlon_degree(df, res):

    df['lon-round'] = roundPartial(df['longitude'], res)
    df['lat-round'] = roundPartial(df['latitude'], res)
    
    return df

def haversine(lat1, lon1, lat2, lon2):
    '''
    # Example usage:
    lat1 = 52.5200
    lon1 = 13.4050
    lat2 = 48.8566
    lon2 = 2.3522

    distance = haversine(lat1, lon1, lat2, lon2)
    print(f"The distance between the two points is {distance} kilometers.")
    '''
    # Radius of the Earth in kilometers
    earth_radius = 6371  # You can also use 3958.8 for miles

    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = earth_radius * c

    return distance

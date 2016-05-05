# -*- coding: utf-8 -*-

"""
Insert data from the csv files obtained from search_for_health_units.py into SQLite Database: Places, Reviews, GoogleMetadata, and AmenityTypes tables. 
"""

import os
import fnmatch
import sqlite3
import csv
import re

fdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "/data/google_data/")

bb = 0
bbname = 'BB%s' %bb
files = fnmatch.filter(os.listdir(fdir), bbname + 'METADATA_*.csv')

conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'NICA.db'))
cur = conn.cursor()

# Data insertion is done as follows: for each search grid (specified by LAT, LON), we first insert a place, specified with google_id into the GoogleMetadata Table. If the insertion fails, skip the current google_id. If the insertion is successful, insert the corresponding place details into Places Table, generating a placeid key. Copy this newly generated key back into the GoogleMetadata Table. If reviews and types are found for this google_id, insert the corresponding entries into Reviews and AmenityTypes tables. 
for filename in files:
    strmatch = re.sub(bbname + 'METADATA_(.*).csv', '\\1', filename)      
    
    with open(os.path.join(fdir, 'METADATA_' + strmatch + '.csv'), encoding='utf-8') as csv_metadata, \
         open(os.path.join(fdir, 'PLACES_' + strmatch + '.csv'), encoding='utf-8') as csv_places:
        
        places_reader = csv.DictReader(csv_places, delimiter=';')
        places = [row for row in places_reader]
        
        if fnmatch.filter(os.listdir(fdir), 'REVIEWS_' + strmatch + '.csv'):
            with open(os.path.join(fdir, 'REVIEWS_' + strmatch + '.csv'), encoding='utf-8') as csv_reviews:
                reviews_reader = csv.DictReader(csv_reviews, delimiter=';')
                reviews = [row for row in reviews_reader]    
        else: reviews = []
        
        if fnmatch.filter(os.listdir(fdir), 'TYPES_' + strmatch + '.csv'):
            with open(os.path.join(fdir, 'TYPES_' + strmatch + '.csv'), encoding='utf-8') as csv_types:
                types_reader = csv.DictReader(csv_types, delimiter=';')
                types = [row for row in types_reader]    
        else: types = []
        
        metadata_reader = csv.DictReader(csv_metadata, delimiter=';')
        for metadata in metadata_reader:
            placeid = None
            google_id = metadata['place_id']
            url = metadata['url']
            scope = metadata['scope']            
            try:
                cur.execute(''' INSERT INTO GoogleMetadata(id, google_id, url, idscope) \
                                VALUES (?, ?, ?, ?);''', (placeid, google_id, url, scope))   
                                
                # Find the row in places (list of all places) with matching place_id
                place = next(filter(lambda x: x['place_id'] == google_id, places))
                if place:
                    name = place['name']
                    lat = place['lat'] if place['lat'] != '' else None
                    lng = place['lng'] if place['lng'] != '' else None
                    source = 'Google'
                    date_retrieved = place['date_retrieved']
                    address = place['formatted_address']
                    streetnumber = place['street_number']
                    streetname = place['street_name']
                    citytown = place['city']
                    province = place['province']
                    postalcode = place['postal_code']
                    phonenum = place['phone_number']
                    website = place['website']
                    permanently_closed = place['permanently_closed']
                    vicinity = place['vicinity']
                    owner = None
                    google_rating = place['rating']
                    
                    try:
                        cur.execute('''INSERT INTO Places(name, lat, lng, source, date_retrieved, address, streetnumber, \
                                                     streetname, citytown, province, postalcode, phonenum, website, \
                                                     permanently_closed, vicinity, owner, google_rating) \
                                            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', \
                                     (name, lat, lng, source, date_retrieved, address, streetnumber, streetname, \
                                     citytown, province, postalcode, phonenum, website, permanently_closed, \
                                     vicinity, owner, google_rating) )
                        
                        placeid = cur.lastrowid   # get the latest generated placeid key
                        
                        print(placeid)
                        
                        # UPDATE GoogleMetadata Table with placeid
                        cur.execute('''UPDATE GoogleMetadata SET id = '%s' WHERE google_id = '%s'; ''' %(placeid, google_id))
                        
                        # Insert reviews and amenity types, if corresponding entries exist
                        for review in filter(lambda x: x['place_id'] == google_id, reviews):
                            author_name = review['author_name']
                            user_rating = review['rating']
                            text = review['text']
                            review_time = review['time']
                            lang = review['language']                            
                            try:
                                cur.execute('''INSERT INTO Reviews(placeid, author_name, user_rating, text, review_time, lang) \
                                            VALUES(?, ?, ?, ?, ?, ?);''', \
                                           (placeid, author_name, user_rating, text, review_time, lang))
                            except sqlite3.Error as e:
                                print("An error occurred when inserting into Reviews table:", e.args[0])
                                print("None is inserted.")
                                
                        for type in filter(lambda x: x['place_id'] == google_id, types):
                            amtype = type['type']
                            source = 'Google'                            
                            try:
                                cur.execute('''INSERT INTO AmenityTypes(placeid, amtype, source) \
                                               VALUES(?, ?, ?);''', (placeid, amtype, source))
                            except sqlite3.Error as e:
                                print("An error occurred when inserting into AmenityTypes table:", e.args[0])
                                print("None is inserted.")
                                
                    except sqlite3.IntegrityError:
                        # If fail to insert, delete the corresponding entry in the metadata table.
                        print('Insertion into Places table failed. Possibly null values in lat, lng. Deleting the corresponding entry in the Metadata table...')
                        # Integrity error... Delete the item in Metadata table
                        cur.execute('''DELETE FROM GoogleMetadata WHERE google_id = '%s'; ''' %google_id)
                else:
                    # Metadata exists but no corresponding place in Place Table, delete the item in metadata table
                    print('Metadata exists but no corresponding entry in the Place table. Deleting the entry from the Metadata table...')
                    cur.execute('''DELETE FROM GoogleMetadata WHERE google_id = '%s';''' %google_id)
                    
            except sqlite3.IntegrityError:
                print('Item already exists. Cannot add twice.')
                
            conn.commit()
    
conn.close()
    
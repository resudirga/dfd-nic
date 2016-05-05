import utilFunctions as uf
import numpy as np
import os, sys

FDIR = os.path.dirname(os.path.realpath(__file__))  

# Search parameters
API_KEY = '###-###' # Get your Google API key from https://developers.google.com/maps/documentation/directions/get-api-key
SEARCH_RADIUS = '4000'
SEARCH_TYPES = 'hospital|health|pharmacy|dentist|doctor|physiotherapist'          
 
# Nicaragua bounding box: Divide the country into boxes and perform the search for each box. Each entry in the following list contains the (NE, SW) geocoordinates of each box. See nic_bounding_boxes.pdf for a depiction of these boxes 
NIC_BOUNDBOXES = [[ (15.03, -83.13), (13.87, -84.93) ],   # 0 [Northheast corner: (lat, lon), Southwest corner: (lat, lon)]
                  [ (14.75, -84.93), (13.87, -85.79) ],   # 1 
                  [ (13.87, -83.41), (12.67, -84.74) ],   # 2 
                  [ (13.87, -84.74), (12.67, -85.70) ],   # 3 
                  [ (12.67, -83.48), (10.68, -84.74) ],   # 4 
                  [ (12.67, -84.74), (10.68, -85.70) ],   # 5
                  [ (12.67, -85.70), (12.18, -87.42) ],   # 6
                  [ (12.18, -85.70), (11.77, -86.76) ],   # 7
                  [ (11.77, -85.70), (11.54, -86.59) ],   # 8
                  [ (11.54, -85.70), (11.07, -86.32) ],   # 9
                  [ (14.10, -85.70), (12.67, -86.60) ],   # 10
                  [ (13.87, -86.60), (12.67, -87.70) ] ]  # 11
                
# For each bounding box, we divide the area into smaller squares, their sides are 5-km long. For each square, we do a radar search centered at the square's center and with search radius of 5/2 *sqrt(2) = 4 km. For each bounding box, create a log file: log_BB{0:9}.txt that reports how many places found in each square. Each square's search results in 4 lists: place, reviews, metadata, and types tables; each of them is written as a csv table with a filename like this: PLACES_LON-86.3675_LAT+11.6550_RAD4000m. Lon, Lat in the filename denotes the centre of the search. Note: Just keep in mind that Google accommodates up to 1000 queries per day, after that the query may fail (returning no place). 
bb_num = 11         
boundbox = NIC_BOUNDBOXES[bb_num]
log_txt = os.path.join(FDIR, "google_data/" + 'log_BB%s' % bb_num + '.txt')
with open(log_txt, 'w', newline='') as txt_log:
    txt_log.write('Logging place search for Bound Box %s: \n' %bb_num)
    # Construct search grids
    left_lon, right_lon = boundbox[1][1], boundbox[0][1]
    top_lat, bottom_lat = boundbox[0][0], boundbox[1][0]  
    ngrid_lon = int(np.ceil((right_lon - left_lon) / 0.05 + 0.5))
    ngrid_lat = int(np.ceil((top_lat - bottom_lat) / 0.05 + 0.5))
    lon_grids = np.linspace(left_lon, right_lon, ngrid_lon)
    lat_grids = np.linspace(top_lat, bottom_lat, ngrid_lat)

    prev_lon, prev_lat = lon_grids[0], lat_grids[0]
    for lon in lon_grids[1:]:
        ctr_lon = prev_lon + (lon - prev_lon) / 2.0
        for lat in lat_grids[1:]:
            ctr_lat = prev_lat + (lat - prev_lat) / 2.0
            
            print('\nSearching for places at lon: %s' %ctr_lon + ', lat:%s ...' % ctr_lat)
            txt_log.write('\nSearching for places at lon: %s' %ctr_lon + ', lat:%s ...' % ctr_lat) 
            
            search_params = {'location' : '%s' %ctr_lat + ',' + '%s' % ctr_lon, 
              'radius' : SEARCH_RADIUS, \
              'types' : SEARCH_TYPES}
            
            places, reviews, metadata, types = uf.search_details_reviews(search_params, API_KEY)
            
            if places:   
                print('%s' %len(places) + ' places found. Writing to files...\n')
                txt_log.write('%s' %len(places) + ' places found. Writing to files...\n')
                outfile_places = os.path.join(FDIR, "google_data/" + \
                                        'BB%s' % bb_num + 'PLACES_' + \
                                        'LON%+03.4f_' %ctr_lon + \
                                        'LAT%+03.4f_' %ctr_lat + 
                                        'RAD%sm' %SEARCH_RADIUS + '.csv')
                                        
                with open(outfile_places, 'w', newline='', encoding='utf-8') as csv_places:
                    fieldnames = uf.get_fieldnames('places')
                    uf.dictlist2csv(places, csv_places, fieldnames)
            else:
                txt_log.write('0 places found. \n')
                    
            if reviews:            
                outfile_reviews = os.path.join(FDIR, "google_data/" + \
                                        'BB%s' % bb_num + 'REVIEWS_' + \
                                        'LON%+03.4f_' %ctr_lon + \
                                        'LAT%+03.4f_' %ctr_lat + 'RAD%sm' %SEARCH_RADIUS + '.csv')
                                        
                with open(outfile_reviews, 'w', newline='', encoding='utf-8') as csv_reviews:
                    fieldnames = uf.get_fieldnames('reviews')
                    uf.dictlist2csv(reviews, csv_reviews, fieldnames)
                    
            if metadata:            
                outfile_metadata = os.path.join(FDIR, "google_data/" + \
                                        'BB%s' % bb_num + 'METADATA_' + \
                                        'LON%+03.4f_' %ctr_lon + \
                                        'LAT%+03.4f_' %ctr_lat + 'RAD%sm' %SEARCH_RADIUS + '.csv')
                                        
                with open(outfile_metadata, 'w', newline='', encoding='utf-8') as csv_metadata:
                    fieldnames = uf.get_fieldnames('metadata')
                    uf.dictlist2csv(metadata, csv_metadata, fieldnames)
                    
            if types:            
                outfile_types = os.path.join(FDIR, "google_data/" + \
                                        'BB%s' % bb_num + 'TYPES_' + \
                                        'LON%+03.4f_' %ctr_lon + \
                                        'LAT%+03.4f_' %ctr_lat + 'RAD%sm' %SEARCH_RADIUS + '.csv')
                                        
                with open(outfile_types, 'w', newline='', encoding='utf-8') as csv_types:
                    fieldnames = uf.get_fieldnames('types')
                    uf.dictlist2csv(types, csv_types, fieldnames)
            
            prev_lat = lat
        prev_lon = lon
                    
                
            
            
            
            
           

# -*- coding: utf-8 -*-
"""
Extract health and education facilities from OpenStreetMap Nicaragua.
Data sources are: 
* nicaragua-latest.osm, 
* managua_nicaragua.imposm-shapefiles/managua_nicaragua_osm_amenities.shp, 
* managua_nicaragua.imposm-shapefiles/managua_nicaragua_osm_buildings.shp
Generate 3 csv tables: osm_places, osm_altnames, osm_addresses
To run, place all source files under a subfolder OSM_DATA/
"""

import os, sys
import xml.etree.cElementTree as ET
import shapefile
import pandas as pd
import re, csv

def xml_count_tags(fpath):
    """ List the tags of all direct children of root as well as their counts """
    counts = dict()
    for event, elem in ET.iterparse(fpath):
        if elem.tag not in counts.keys():
            counts[elem.tag] = 1
        else:
            counts[elem.tag] += 1
    return counts
    
def xml_list_node_tags(fpath, out_filename):
    """ List all "k" attributes of node/tag elements """
    fields = []
    for event, elem in ET.iterparse(fpath):
        if elem.tag == 'node':
            tags = elem.findall('tag')
            if tags: 
                for tag in tags:
                    new_item = tag.attrib["k"]
                    if new_item not in fields:
                        fields.append(new_item) 
    fields.sort()
    with open(out_filename, 'w') as txt:
        for field in fields:
           txt.write(field + '\n')   
    return fields

def get_regexp(type):
    regexp = None
    if type == 'health':
        regexp = re.compile( 'hos?pital|dentist|pharmacy|farma|laborator|cl?n?c|\
                  medic|optic|hospice|doctor|puesto m.?dico|puesto de salud|\
                  centro de salud|centro m.?dic.?|unidad m.?dic.?|m.?dico.? unid.*|\
                  health_post|health_cent[er][re]|\
                  health_facility:type|health_specialty' )
    elif type == 'education':
        regexp = re.compile('universidad|university|escuela|school|college|colegio|\
                             academy|escolar|kindergarten')
    return regexp

def classify_amenity_type(name):
    """ Given a string (name), use it to classify its amenity and facility types """
    
    name = name.lower()
    amenity_type = None
    facility_type = None
    
    # amenity_type = health
    regexp = get_regexp('health')
    if regexp.search(name):
        amenity_type = 'health'
        facility_type = classify_facility_type(name, 'health')
                
    # amenity_type = education
    regexp = get_regexp('education')
    if regexp.search(name):
        amenity_type = 'education'
        facility_type = classify_facility_type(name, 'education')
    
    assert isinstance(amenity_type, str) or not amenity_type, "amenity_type should be a string or None"
    assert isinstance(facility_type, str) or not facility_type, "facility_type should be a string  or None"
    return amenity_type, facility_type 
    
def classify_facility_type(name, type):
    """ Classify facility type from its name, given a known amenity type (e.g., health, education) """
    facility_type = None
    if type == 'health' :
        if re.search('hos?pital', name) : facility_type = 'hospital'
        elif re.search('dentist', name) : facility_type = 'dentist'
        elif re.search('pharmacy|farma', name) : facility_type = 'pharmacy'
        elif re.search('cl?n?c', name) : facility_type = 'clinic'
        elif re.search('puesto m.?dico|puesto de salud|health post', name) : facility_type = 'health_post'
        elif re.search('centro de salud|centro m.?dic.?|unidad m.?dic.?|m.?dico.? unid.*', name): facility_type = 'health_centre'
        elif re.search('laborator', name) : facility_type = 'laboratory'
        elif re.search('doctor|medic', name) : facility_type = 'medic'
        elif re.search('maternas|maternity', name) : facility_type = 'maternity_home'
        elif re.search('hospice', name) : facility_type = 'other:hospice'
        elif re.search('optic', name) : facility_type = 'other:optic'
        
    elif type == 'education' :
        if re.search('universidad|university', name) : facility_type = 'university'
        elif re.search('escuela|school|college|colegio|academy|escolar|kindergarten', name) : 
            facility_type = 'school'
            
    return facility_type
    
def xml_is_amenity(elem):
    """ 
    Check if a tree element with a tag 'node' corresponds to an amenity. Currently, only education and health types are supported.
    Return: is_amenity (bool), place (a dictionary containing the amenity's information; None if not an amenity) 
    """ 
    is_amenity = False
    place = None
    
    tags = elem.findall('tag')
    if tags:
        names = []
        amenity_type = None
        facility_type = None
        address_dict = { 'full_addr' : None,
                         'housename' : None,
                         'building_no' : None,
                         'street' : None,
                         'district' : None,
                         'city' : None,
                         'province' : None,
                         'country' : 'Nicaragua',
                         'postal_code' : None
                        }        
        for tag in tags:
            key = str(tag.get("k")).lower()
            val = str(tag.get("v"))
            
            # name
            regexp = re.compile('^name|alt_name|official_name|\
                           old_name|int_name|loc_name|reg_name|short_name')
            if regexp.search(key):
                names.append(val)

            # address
            regexp = re.compile('addr:.*|postal_code|is_in')
            if regexp.search(key):
                if re.search('addr:|is_in:', key):
                    address_dict['full_addr'] = val if re.match('addr:full|addr:postal', key) else None
                    address_dict['building_no'] = val if re.match('addr:buildingnumber|addr:housenumber', key) else None
                    address_dict['street'] = val if re.match('addr:street', key) else None
                    address_dict['housename'] = val if re.match('addr:housename', key) else None
                    address_dict['district'] = val if re.match('addr:district', key) else None
                    address_dict['city'] = val if re.match('addr:city', key) else None
                    address_dict['province'] = val if re.match('addr:province|is_in:state', key) else None
                    address_dict['postal_code'] = val if re.match('addr:postcode', key) else None
                else: # re.search('postal_code', key):   
                    address_dict['postal_code'] = val if re.match('postal_code', key) else None
            
            # AMENITY_TYPE and FACILITY_TYPE
            # ----- Search at node/tag.key
            # Health
            regexp = re.compile('healthcare|health_facility:type|health_specialty|hos?pital|\
            doctor|cl?n?c|dentist|pharma|farma')
            if regexp.search(key):
                amenity_type = 'health'
                if re.search('health_facility:type|healthcare', key):
                    facility_type = val
                elif re.search('health_specialty:.*', key):
                    facility_type = re.sub('health_specialty:(.*)', '\\1', key)
                else: # re.search('hos?pital|doctor|cl?nic*|dentist|farma|pharma', key):
                    facility_type = key 
            
            # Education
            regexp = re.compile('education|school')
            if regexp.search(key):
                amenity_type = 'education'
                if key == 'education': facility_type = val
                else: facility_type = 'school:' + val
                    
            # ----- Search at the attribute value ("v") of node/tag."k"=="amenity"
            if re.search('amenity', key):                        
                # Health
                regexp = re.compile('hos?pital|cl?n?c|laborator|pharmacy|\
                health_post|health_cent[er][re]|doctor|dentist|\
                optic|medic|hospice')
                          
                if regexp.search(val):
                    amenity_type = 'health'
                    if re.search('hos?pital|dentist|pharmacy|cl?n?c|\
                    medic|optic|hospice|doctor', val):
                        facility_type = val
                    elif re.search('laborator', val):
                        facility_type = 'laboratory'
            
                # Education
                regexp = re.compile('school|university|kindergarten|college')
                if regexp.search(val):
                    amenity_type = 'education'
                    facility_type = val
        # End of for loop ----------
        
        # At the moment, we only add places that can be classified as health or education
        # Some items have had their amenity_type and facility_type tags filled. However, we can also find information about amenity/facility type by its name.        
        if amenity_type or names:
            if amenity_type: 
                is_amenity = True
            else:
                # Classify amenity by its name
                for name in names:
                    amenity_type, facility_type = classify_amenity_type(name)
                    if amenity_type:
                        is_amenity = True
                        break
            
            # add to places if amenity_type is not empty             
            place = { '_id' : elem.get('id'),
                      'created' : {'version' : elem.get('version'),
                                   'ts' : elem.get('timestamp'),
                                   'changeset' : elem.get('changeset'),
                                   'uid' : elem.get('uid'),
                                   'user' : elem.get('user')
                                   },
                      'names' : names,                 # required
                      'amenity_type' : amenity_type,   # required
                      'facility_type': facility_type, 
                      'location' : { 'lat' : elem.get('lat') , 'lon' : elem.get('lon') }, # required
                      'address' : address_dict
                    }
    return is_amenity, place    
    
def xml_validate_amenity(amenity_dict):
    """
    Validate an amenity_dict as returned by xml_is_amenity(elem)
    Run a check if a certain amenity entry is valid. For example, many fast food restaurants are tagged with amenity_type = 'health' and facility_type = internet_access. This function should return False if such entry is found. 
    ATM, Only health type is supported.
    Return True/False
    """
    is_valid = False
    
    type = amenity_dict['amenity_type']
    names = amenity_dict['names']
    facility_type = amenity_dict['facility_type']
    
    if type == 'health':
        # if facility_type does not contain internet or access
        if facility_type and not re.search('internet|access', facility_type): 
            is_valid = True
        else:  # facility_type does not exist or facility_type = 'internet|access'
            # Use name to classify the facility - its name must contain health facility keywords to be categorized as a health facility 
            for name in names:
                amenity_type, facility_type = classify_amenity_type(name)
                if amenity_type == 'health':
                    is_valid = True 
                    break
    
    elif type == 'education': # Not implemented yet, pass everything through
        is_valid = True

    return is_valid
    
def xml_get_amenities(fpath):
    """ 
    Given OSM Nicaragua XML file, return all facilities related to health and education.
    Return : places (a list of dicts containing information about each facility), count (number of facilities found)
    """   
    places = []
    count = 0
    for event, elem in ET.iterparse(fpath):
        if elem.tag == 'node':
            amenity_flag, amenity = xml_is_amenity(elem)
            if amenity_flag:
                if xml_validate_amenity(amenity):
                    places.append(amenity)
                    count += 1
    return places, count

def xml_get_tables(amenities_dicts):
    """ 
    Transform amenities_dicts into 3 lists of dictionaries (tables): places, altnames, and addresses
    Each table has a prescribed key value pairs.
    """       
    places, altnames, addresses = [], [], []
    
    for facility in amenities_dicts:
        # Municipality, department, and country
        # District, city and municipality are the same. Use one of them as municipality.
        if facility['address']['city']:
            municipality = facility['address']['city']
        elif facility['address']['district']:
            municipality = facility['address']['district']
        else: municipality = ''
        department = facility['address']['province']
        country = 'Nicaragua' 
        
        # Add to places.csv
        new_place = {'osm_id' : facility['_id'],
                    'name' : facility['name'][0] if facility['name'] else '', 
                    'type' : facility['amenity_type'],
                    'facility_type' : facility['facility_type'],
                    'lat' : facility['location']['lat'],
                    'lon' : facility['location']['lon'],
                    'municipality' : municipality,
                    'department' : department,
                    'country'    : country
                   }
        places.append(new_place)
        
        # Add to altnames.csv
        if facility['name']:
            for name in facility['name']:
                new_altname =  { 'osm_id' : facility['_id'],
                                 'name'   : name }
                altnames.append(new_altname)
        
        # Add to addresses.csv
        address = facility['address']
        if address:
            if address['full_addr']:
                full_addr = address['full_addr']
            else:
                building_no = address['building_no']
                street = address['street']
                if building_no and street:
                    full_addr = address['building_no'] + "," + address['street']
                else: full_addr = ''
                
            new_address = { 'osm_id'    : facility['_id'],
                            'full_addr' : full_addr,
                            'postal_code'  : address['postal_code'],
                            'municipality' : municipality,
                            'department'   : department,
                            'country'      : country
                           }
            addresses.append(new_address) 
    return places, altnames, addresses
                
def print_tables(places, altnames, addresses):
    """ 
    Print places, altnames, and addresses tables into csv files
    """       
    # Column names of each table
    colnames = { 'places' : ['osm_id', 'name', 'type', 'facility_type', \
                             'lat', 'lon', 'municipality', 'department', 'country'],
                 'altnames' : ['osm_id', 'name'],
                 'addresses' : ['osm_id', 'full_addr', 'postal_code', 'municipality', 'department', 'country']
                }
        
    fpath_places = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'osm_places.csv')
    fpath_altnames = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'osm_altnames.csv')
    fpath_addresses = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'osm_addresses.csv')
    
    csvargs = {'newline': '', 'encoding': 'utf-8'}
    with open(fpath_places,'w', **csvargs) as csv_places,\
         open(fpath_altnames,'w', **csvargs) as csv_altnames,\
         open(fpath_addresses,'w', **csvargs) as csv_addresses:
        
        dwargs = {'delimiter' : ",", 'quotechar' : '"'}        
        writers = [ csv.DictWriter(csv_places, colnames['places'], **dwargs), 
                    csv.DictWriter(csv_altnames, colnames['altnames'], **dwargs),
                    csv.DictWriter(csv_addresses, colnames['addresses'], **dwargs) ]
        tables = [places, altnames, addresses]
        
        for writer, table in zip(writers, tables):
            writer.writeheader()
            writer.writerows(table) 
            
def process_xml(folder_path):
    """ 
    Parse and transform nicaragua-latest.osm file.
    Return 3 tables: places, altnames, addresses
    """
    fpath = os.path.join(folder_path, "nicaragua-latest.osm")
    amenities, count = xml_get_amenities(fpath) 
    print('nicaragua-latest.osm : Found ' + str(count) + ' facilities \n')
    
    places, altnames, addresses = xml_get_tables(amenities)    
    return places, altnames, addresses

def process_amenities_shp(folder_path):
    """ 
    Transform managua_nicaragua_osm_amenities shapefiles into a data structure similar to places_xml_table
    """
    places = []
                       
    shp_fpath = os.path.join(folder_path, "managua_nicaragua_osm_amenities")
    shpreader = shapefile.Reader(shp_fpath)
    
    shapes = shpreader.shapes()
    records = shpreader.records()  # Each record contains ['id', 'osm_id', 'name', 'type']
    
    places = []
    for shape, record in zip(shapes, records):
        lon, lat = shape.points[0][0], shape.points[0][1]
        osm_id = record[1]
        name = record[2] if isinstance(record[2], str) else ''
        temp_type = record[3] if isinstance(record[3], str) else ''
        
        # type contains the following values: university, fuel, library, school, hospital, fire_station, police, townhall. However, many health facilities were classified as hospitals even though they are not. Classify facility_type by its name
        if temp_type == 'hospital':
            type = 'health'
            facility_type = classify_facility_type(name, 'health') if name else None
        elif temp_type in ['university', 'school'] :
            type = 'education'
            facility_type = temp_type
        else:
            type = 'other'
            facility_type = temp_type
        
        new_place = {'osm_id' : osm_id,
                    'name' : name, 
                    'type' : type,
                    'facility_type' : facility_type,
                    'lat' : lat,
                    'lon' : lon,
                    'municipality' : 'Managua',
                    'department' : 'Managua',
                    'country'    : 'Nicaragua'
                    }
        
        places.append(new_place)
    return places 

def print_man_amenities(managua_amenities):
    """ Print amenities extracted from managua_nicaragua_osm_amenities.shp into a csv file """
    colnames = ['osm_id', 'name', 'type', 'facility_type', \
                'lat', 'lon', 'municipality', 'department', 'country']
    
    fpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'managua_places1.csv')
    with open(fpath,'w', newline='', encoding='utf-8') as csv_places:
        writer = csv.DictWriter(csv_places, colnames, delimiter=",", quotechar='"')
        writer.writeheader()
        writer.writerows(managua_amenities) 
        
def process_buildings_shp(folder_path):
    """ 
    Transform managua_nicaragua_osm_buildings shapefiles into a data structure similar to xml_places_table
    """
    places = []
                       
    shp_fpath = os.path.join(folder_path, "managua_nicaragua_osm_buildings")
    shpreader = shapefile.Reader(shp_fpath)
    
    shapes = shpreader.shapes()
    records = shpreader.records()  # Each record contains ['id', 'osm_id', 'name', 'type']
    
    places = []
    for shape, record in zip(shapes, records):
        lon, lat = shape.points[0][0], shape.points[0][1]
        osm_id = record[1]
        name = record[2] if isinstance(record[2], str) else ''
        temp_type = record[3] if isinstance(record[3], str) else ''
        
        # type contains the following values: university, fuel, library, school, hospital, fire_station, police, townhall. However, many health facilities were classified as hospitals even though they are not. Classify facility_type by its name
        temp_type = temp_type.lower()
        if temp_type in ['hospital', 'salud']:
            type = 'health'
            facility_type = classify_facility_type(name, 'health') if name else None
        elif get_regexp('education').search(temp_type):
            type = 'education'
            facility_type = classify_facility_type(temp_type, 'education')
        elif temp_type in ['church', 'chapel']:
            type = 'community'
            facility_type = 'church'
        elif temp_type in ['yes', 'no']:
            if name: 
                type, facility_type = classify_amenity_type(name)
            else:
                type, facility_type = None, None
        else:
            type = 'other'
            facility_type = temp_type
            
        if type:
            new_place = {'osm_id' : osm_id,
                         'name' : name, 
                         'type' : type,
                         'facility_type' : facility_type,
                         'lat' : lat,
                         'lon' : lon,
                         'municipality' : 'Managua',
                         'department' : 'Managua',
                         'country'    : 'Nicaragua'
                        }
            places.append(new_place)
    return places 
    
def main():
    """ 
    Process all data sources and generate 3 tables: osm_places, osm_altnames, osm_addresses, 
    then print all tables into csv files of the same names
    """
    # DATA SOURCE #1: nicaragua-latest.osm
    folder_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "OSM_DATA/nicaragua-latest.osm/")
    places_1, altnames, addresses = process_xml(folder_dir)
    
    # DATA SOURCE #2: managua_nicaragua_osm_amenities.shp
    folder_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "OSM_DATA/managua_nicaragua.imposm-shapefiles/")
    places_2 = process_amenities_shp(folder_dir)
    
    # DATA SOURCE #3: managua_nicaragua_osm_buildings.shp
    folder_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "OSM_DATA/managua_nicaragua.imposm-shapefiles/")
    places_3 = process_buildings_shp(folder_dir)
    
    # Combine data sources #1, #2 and #3 then print
    places_combined = []
    for places in [places_1, places_2, places_3]:
        places_combined.extend(places)
    
    print_tables(places_combined, altnames, addresses)
    
if __name__ == "__main__":
    main()
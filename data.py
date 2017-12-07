import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

#sample.osm is a small sample of "boston_massachusetts.osm", made by extracting every kth top level from "boston_massachusetts.osm"
#Validation is ~ 10X slower, the small sample is used when the the project takes validating process.
#OSM_PATH = "sample.osm"
OSM_PATH = "boston_massachusetts.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"


LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

#Dictionary for overabbreviated street names correction
mapping = { "St": "Street",
            "St.": "Street",
            "St,":"Street",
            "ST":"Street",
            "Street.":"Street",
            "st":"Street",
            "street":"Street",
            "Ave": "Avenue",
            "Ave.":"Avenue",
            "Ct":"Court",
            "Dr":"Drive",
            "Rd":"Road",
            "Rd.": "Road",
            "rd.":"Road",
            "Pkwy":"Parkway"}

#Function for correcting overabbreviated street names
def change_street_name(mapping, street_name):
    keys=mapping.keys()
    #To avoid only correcting part of a word, split street names into words and then iterate over each word, correcting them to their mapping  
    name_array=street_name.split()
    for i,elem in enumerate(street_name):
        if elem in keys:
            name_array[i]=mapping[elem]
    #Join corrected words into street names again    
    rename=' '.join(name_array)    
    return rename

#check if the attribute is street name
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")    
    
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    # YOUR CODE HERE
    
    if element.tag == 'node':
        #Return a dictionary of top level node attributes for "node" field
        for node_field in NODE_FIELDS:
            node_attribs[node_field]=element.attrib[node_field]
        node_tag={}
        
        #Return a list of dictionaries, one per secondary tag for "node_tags" field
        for tag in element.iter("tag"):            
            #If the attribute is street name, correct overabbreviated street names first
            if is_street_name(tag):
                tag_value=change_street_name(mapping, tag.attrib['v'])
            else:
                tag_value=tag.attrib['v']            
            node_tag['id']=element.attrib['id']
            node_tag['value']=tag_value
            #Assign "key" value in "node_tags" field dictionary the full tag "k" attribute value if no colon is present or the characters after the colon if one is
            #Assign "type" value in "node_tags" field dictionary the full tag "k" either the characters before the colon in the tag "k" value or "regular" if a colon is not present
            if ":" in tag.attrib['k']:
                index=(tag.attrib['k']).find(':')
                node_tag['key']=(tag.attrib['k'])[(index+1):]
                node_tag['type']=(tag.attrib['k'])[:index]
            else:
                node_tag['key']=tag.attrib['k']
                node_tag['type']="regular"
            tags.append(node_tag)
            node_tag={}
        return {'node': node_attribs, 'node_tags': tags}
    
    elif element.tag == 'way':
        #Return a dictionary of top level node attributes for "way" field
        for way_field in WAY_FIELDS:
            way_attribs[way_field]=element.attrib[way_field]
        
        #Return a dictionary for "way_nodes" field
        way_node={}
        position=0   #Recording the index starting at 0 of the nd tag
        for tag in element.iter("nd"):
            way_node['id']=element.attrib['id']
            way_node['node_id']=tag.attrib['ref']
            way_node['position']=position
            way_nodes.append(way_node)
            position=position+1
            way_node={}
        
        #Return a list of dictionaries, one per secondary tag for "way_tags" field
        way_tag={}
        for tag in element.iter("tag"):
            #If the attribute is street name, correct overabbreviated street names first
            if is_street_name(tag):
                tag_value=change_street_name(mapping, tag.attrib['v'])
            else:
                tag_value=tag.attrib['v']  
            way_tag['id']=element.attrib['id']
            way_tag['value']=tag_value
            #Assign "key" value and "type" value, the same as for "node_tags"fields
            if ":" in tag.attrib['k']:
                index=(tag.attrib['k']).find(':')
                way_tag['key']=(tag.attrib['k'])[(index+1):]
                way_tag['type']=(tag.attrib['k'])[:index]
            else:
                way_tag['key']=tag.attrib['k']
                way_tag['type']="regular"
            tags.append(way_tag)
            way_tag={}
        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    #use 'wb' instead of 'w', or there will be empty interval lines in csv file, making it difficult to turn csv file into sql
    with codecs.open(NODES_PATH, 'wb') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'wb') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'wb') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'wb') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'wb') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])



# Note: Validation is ~ 10X slower. For the project consider using a small
# sample of the map when validating.
#process_map(OSM_PATH, validate=True)
process_map(OSM_PATH, validate=False)
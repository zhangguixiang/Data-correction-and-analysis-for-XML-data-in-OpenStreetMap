"""
Your task in this exercise has two steps:

- audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix 
    the unexpected street types to the appropriate ones in the expected list.
    You have to add mappings only for the actual problems you find in this OSMFILE,
    not a generalized solution, since that may and will depend on the particular area you are auditing.
- write the update_name function, to actually fix the street name.
    The function takes a string with street name as an argument and should return the fixed name
    We have provided a simple test so that you see what exactly is expected
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "boston_massachusetts.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

#Expected street types
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]



#Return a dictionary with unexpected street types as key and corresponding street name data set as values
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
#Return a data set with state name not being "Massachusetts"
def audit_state_name(unexpected_state_names,state_name):
    if state_name != "Massachusetts":
        unexpected_state_names.add(state_name)

#check if the attribute is street name            
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")
#check if the attribute is state name
def is_state_name(elem):
    return (elem.attrib['k']=="addr:state")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    unexpected_state_names=set([])
    for event, elem in ET.iterparse(osm_file):
        #Audit for every node and way element
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                if is_state_name(tag):
                    audit_state_name(unexpected_state_names,tag.attrib['v'])
    osm_file.close()
    return street_types,unexpected_state_names






st_types,unexpected_state = audit(OSMFILE)
pprint.pprint(dict(st_types))
pprint.pprint(unexpected_state)

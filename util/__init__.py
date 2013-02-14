# General Utility functions
import sys

from lxml import etree
import copy
import json
from project import Project

class ProjectJSONEncoder(json.JSONEncoder):

    def default(self, x):
        if isinstance(x, Project):
            return x.__dict__
        else:
            return json.JSONEncoder.default(self, obj)


def open_xml(path):
    with open(path, "rb") as f:
        return etree.parse(f)

def serialize_manifest(node, path):
    if path == '-':
        node.write(sys.stdout, xml_declaration=True, encoding='UTF-8')
    elif hasattr(path, 'write'):
        node.write(path, xml_declaration=True, encoding='UTF-8')
    else:
        with open(path, 'wb+') as f:
            node.write(path, xml_declaration=True, encoding='UTF-8')

def filter_manifest(node, filters):
    new_node = copy.deepcopy(node)
    for f in filters:
        attr, raw_list = f.split(':', 1)
        attr_list = raw_list.split(',')

        for p in new_node.findall('project'):
            if attr[0] == '^' and p.get(attr[1:]) in attr_list:
                p.getparent().remove(p)
            elif attr[0] != '^' and not p.get(attr) in attr_list:
                p.getparent().remove(p)
    return new_node


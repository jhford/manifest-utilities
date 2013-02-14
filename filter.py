from util import open_xml, serialize_manifest, filter_manifest

def filter(f, output, filters):
    node = open_xml(f)
    node = filter_manifest(node, filters)
    serialize_manifest(node, output)


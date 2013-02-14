from util import open_xml, serialize_manifest, filter_manifest


def tidy_remotes(node):
    used_remotes = [node.find('default').get('remote')]
    for project in node.findall('project'):
        if not project.get('remote') in used_remotes:
            used_remotes.append(project.get('remote'))

    for remote in node.findall('remote'):
        if not remote.get('name') in used_remotes:
            remote.getparent().remove(remote)


def cleanup(f, output, filters):
    node = open_xml(f)
    if filters:
        node = filter_manifest(node, filters)
    tidy_remotes(node)
    serialize_manifest(node, output)


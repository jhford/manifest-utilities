import os
import subprocess as sp

from util import open_xml, serialize_manifest

def revision_from_project(path):
    return sp.check_output(["git", "rev-parse", "HEAD"], cwd=path).strip()


def freeze(f, output, b2g_root, gaia_branch, gecko_branch, moz_remotes=[], moz_branch=[]):
    node = open_xml(f)
    default_remote = node.find('default').get('remote')
    for p in node.findall('project'):
        if p.get('path') == 'gecko':
            p.set('revision', gecko_branch)
        elif p.get('path') == 'gaia':
            p.set('revision', gaia_branch)
        elif p.get('remote') in moz_remotes:
            p.set('revision', moz_branch)
        elif p.get('remote', None) == None and default_remote in moz_remotes:
            p.set('revision', moz_branch)
        else:
            rev = revision_from_project(os.path.join(b2g_root, p.get('path')))
            if p.get('revision') and p.get('revision') != rev:
                p.set('upstream', p.get('revision'))
            p.set('revision', rev)
    serialize_manifest(node, output)

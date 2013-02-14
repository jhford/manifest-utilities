#!/usr/bin/env python

import sys
import os
import optparse
import shutil
from lxml import etree
import urlparse
import json
import copy

# This is the directory where temporary files should live
WORKDIR=os.path.join(os.getcwd(), 'repo-contents')

# Features I want:
#   1. What is the list of fully expanded manifests to fetch
#   2. What are the differences between two manifests before expanding
#   3. What are the file differences between the two different manifests

important_nodes = {'remote': ['name', 'alias', 'fetch'],
                   'default': ['remote', 'revision', 'sync-j', 'sync-c', 'sync-s'],
                   'project': ['name', 'path', 'remote', 'revision', 'groups', 'sync-c', 'sync-s', 'upstream'],
                   'annotation': ['name', 'value', 'keep'],
                   'include': ['name']}

class Project(object):
    def __init__(self, path, revision, remote, url, upstream):
        object.__init__(self)
        self.path = path
        self.revision = revision
        self.remote = remote
        self.url = url
        self.upstream = upstream

    def __eq__(self, other):
        return \
                self.url[:-4] if self.url.endswith('.git') else self.url == \
                other.url[:-4] if other.url.endswith('.git') else other.url and \
                self.path == other.path and \
                self.revision == other.revision and \
                self.remote == other.remote and \
                self.upstream == other.upstream

    def differences(self, other):
        d = []
        if self.path != other.path:
            d.append("path ('%s' vs '%s')" % (self.path, other.path))
        if self.revision != other.revision:
            d.append("revision ('%s' vs '%s')" % (self.revision, other.revision))
        if self.remote != other.remote:
            d.append("remote ('%s' vs '%s')" % (self.remote, other.remote))
        if self.url != other.url:
            d.append("url ('%s' vs '%s')" % (self.url, other.url))
        if self.upstream != other.upstream:
            d.append("upstream ('%s' vs '%s')" % (self.upstream, other.upstream))
        return d


    def __str__(self):
        return "GIT Project: path='%(path)s', revision='%(revision)s', remote='%(remote)s', url='%(remote)s', upstream='%(upstream)s" % self.__dict__


class ProjectJSONEncoder(json.JSONEncoder):

    def default(self, x):
        if isinstance(x, Project):
            return x.__dict__
        else:
            return json.JSONEncoder.default(self, obj)

def project_differences(left, right):
    d = {}
    s = {}
    if left.path != right.path:
        d["path"] = {'left': left.path, 'right': right.path}
    else:
        s["path"] = left.path
    if left.revision != right.revision:
        d["revision"] = {'left': left.revision, 'right': right.revision}
    else:
        s["revision"] = left.revision
    if left.remote != right.remote:
        d["remote"] = {'left': left.remote, 'right': right.remote}
    else:
        s["remote"] = left.remote
    if left.url != right.url:
        d["url"] = {'left': left.url, 'right': right.url}
    else:
        s["url"] = left.url
    if left.upstream != right.upstream:
        d["upstream"] = {'left': left.upstream, 'right': right.upstream}
    elif left.upstream != None:
        s["upstream"] = left.upstream

    return {'different': d, 'same': s}


def open_xml(path):
    with open(path, "rb") as f:
        return etree.parse(f)

def serialize_manifest(node, path):
    with open(path, 'wb+') as f:
        node.write(manifest, xml_declaration=True, encoding='UTF-8')

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


def resolve_manifest(node, filters=None, exclude=True):
    if filters:
        node = filter_manifest(node, filters)

    default_node = node.find('default')
    default_remote = default_node.get('remote')
    default_remote_url = node.find(".//remote[@name='%s']" % default_remote).get('fetch')
    default_revision = default_node.get('revision', 'HEAD')

    projects = {}

    for p_node in node.findall('project'):
        if p_node.get('remote'):
            url_base = node.find(".//remote[@name='%s']" % p_node.get('remote')).get('fetch')
        else:
            url_base = default_remote_url

        # This is what repo does, seems legit
        if url_base.index(':') == url_base.index('/')-1:
            url_base = "gopher://" + url_base
        url = urlparse.urljoin(url_base, p_node.get('name'))
        if url.startswith('gopher://'):
            url = url[9:]

        p = Project(path=p_node.get('path'),
                    revision=p_node.get('revision', default_revision),
                    remote=p_node.get('remote', default_remote),
                    url=url,
                    upstream=p_node.get('upstream', None)
        )
        projects[p.path] = p
    return projects


def print_summary(same, only_in_left, only_in_right, different, left_name, right_name):
    if not 'left' in left_name:
        left_name += ' (left)'
    if not 'right' in right_name:
        right_name += ' (right)'
    print "No differences for:"
    print "\n".join(["  * '%s'" % x.path for x in same])

    print "Only in %s:" % left_name
    for only_l in only_in_left:
        print "  * '%s'" % only_l.path

    print "Only in %s:" % right_name
    for only_r in only_in_right:
        print "  * '%s'" % only_r.path

    print "Different:"
    for d in different:
        print "  * '%s' -- %s vs %s" % (d[0].path, left_name, right_name)
        diffs = project_differences(d[0], d[1])
        for d in diffs['different'].keys():
            print "    * %s: '%s' vs '%s'" % (d, diffs['different'][d]['left'], diffs['different'][d]['right'])
        for s in [x for x in diffs['same'].keys() if x != 'path']:
            print "    * %s: %s is the same" % (s, diffs['same'][s])

def print_json_summary(same, only_in_left, only_in_right, different, left_name, right_name):
    diffs = {'left_name': left_name, 'right_name': right_name,
             'same': same,
             'only_in_left': only_in_left,
             'only_in_right': only_in_right}
    diffs['differences'] = {}
    for l,r in different:
        diffs['differences'][l.path] = project_differences(l,r)
    print json.dumps(diffs, cls=ProjectJSONEncoder, indent=2)


def diff_manifest_content(left, right, output_func=print_summary, filters=None):
    left_projects = resolve_manifest(open_xml(left), filters)
    right_projects = resolve_manifest(open_xml(right), filters)

    left_name = os.path.split(left.rstrip(os.sep))[1]
    right_name = os.path.split(right.rstrip(os.sep))[1]


    only_in_left = []
    only_in_right = []
    in_both_sides = [] # list of paths that are on both sides
    different = [] # list of L/R pairs
    same = []

    for l_key in sorted(left_projects.keys()):
        if l_key not in right_projects.keys():
            only_in_left.append(left_projects[l_key])
        else:
            in_both_sides.append(l_key)
    for r_key in sorted(right_projects.keys()):
        if r_key not in left_projects.keys():
            only_in_right.append(right_projects[r_key])

    for key in in_both_sides:
        if left_projects[key] == right_projects[key]:
            same.append(left_projects[key])
        else:
            different.append((left_projects[key], right_projects[key]))


    output_func(same, only_in_left, only_in_right, different, left_name, right_name)



def clean():
    return shutil.rmtree(WORKDIR)

def main():
    parser = optparse.OptionParser("%prog - I diff repo manifests")
    parser.add_option("--filter", dest="filters", action="append")
    parser.add_option("--diff", "-d", dest="diff", action="store_false", default=True)
    parser.add_option("--format", dest="out_format", default="stdout")
    options, args = parser.parse_args()

    if len(args) != 2:
        print >> sys.stderr, "ERROR: must specify exactly two arguments (left and right)"
        parser.exit(1)

    for i in (0,1):
        if not os.path.exists(args[i]) or os.path.isdir(args[i]):
            print >> sys.stderr, "ERROR: %s is not a valid file or is a directory" % args[i]
            parser.exit(1)


    # Once there are more modes, this should error out if more than one mode is specified
    if options.diff:
        if options.out_format.lower() == 'json':
            out_func = print_json_summary
        elif options.out_format.lower() == 'stdout':
            out_func = print_summary
        else:
            print >> sys.stderr, "ERROR: Invalid output format selected"
        diff_manifest_content(args[0], args[1], out_func, filters=options.filters)




if __name__ == "__main__":
    main()

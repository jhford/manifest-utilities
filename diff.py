#!/usr/bin/env python

import sys
import os
import optparse
import urlparse
from util import open_xml, filter_manifest, ProjectJSONEncoder
from project import Project, project_differences
import json



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


def print_summary(output, same, only_in_left, only_in_right, different, left_name, right_name):
    summary=[]
    if not 'left' in left_name:
        left_name += ' (left)'
    if not 'right' in right_name:
        right_name += ' (right)'
    summary.append("No differences for:")
    if len(same) > 0:
        summary.append("\n".join(["  * '%s'" % x.path for x in same]))

    summary.append("Only in %s:" % left_name)
    for only_l in only_in_left:
        summary.append("  * '%s'" % only_l.path)

    summary.append("Only in %s:" % right_name)
    for only_r in only_in_right:
        summary.append("  * '%s'" % only_r.path)

    summary.append("Different:")
    for d in different:
        summary.append("  * '%s' -- %s vs %s" % (d[0].path, left_name, right_name))
        diffs = project_differences(d[0], d[1])
        for d in diffs['different'].keys():
            summary.append("    * %s: '%s' vs '%s'" % (d, diffs['different'][d]['left'], diffs['different'][d]['right']))
        for s in [x for x in diffs['same'].keys() if x != 'path']:
            summary.append("    * %s: %s is the same" % (s, diffs['same'][s]))
    print >> output, "\n".join(summary)


def print_json_summary(output, same, only_in_left, only_in_right, different, left_name, right_name):
    diffs = {'left_name': left_name, 'right_name': right_name,
             'same': same,
             'only_in_left': only_in_left,
             'only_in_right': only_in_right}
    diffs['differences'] = {}
    for l,r in different:
        diffs['differences'][l.path] = project_differences(l,r)
    print json.dumps(diffs, cls=ProjectJSONEncoder, indent=2, sort_keys=True)


def diff_manifest_content(left, right, output_func, output, filters=None):
    left_projects = resolve_manifest(open_xml(left), filters)
    right_projects = resolve_manifest(open_xml(right), filters)

    left_name = os.path.split(left.rstrip(os.sep))[1]
    right_name = os.path.split(right.rstrip(os.sep))[1]

    only_in_left = [] # list of projects that are only on the left
    only_in_right = [] # ditto, right
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

    if hasattr(output, 'write'):
        output_func(output, same, only_in_left, only_in_right, different, left_name, right_name)
    else:
        with open(output, 'wb') as f:
            output_func(f, same, only_in_left, only_in_right, different, left_name, right_name)


def diff(left, right, output, output_format, filters):
    for i in (left, right):
        if os.path.isdir(i):
            print >> sys.stderr, "ERROR: %s is a directory" % args[i]
            parser.exit(1)

    # Once there are more modes, this should error out if more than one mode is specified
    if output_format.lower() == 'json':
        out_func = print_json_summary
    elif output_format.lower() == 'report':
        out_func = print_summary
    else:
        print >> sys.stderr, "ERROR: Invalid output format selected"
        sys.exit(1)

    if not output:
        output = sys.stdout
    diff_manifest_content(left, right, out_func, output=output, filters=filters)


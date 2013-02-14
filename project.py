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

    def __str__(self):
        return "GIT Project: path='%(path)s', revision='%(revision)s', remote='%(remote)s', url='%(remote)s', upstream='%(upstream)s" % self.__dict__


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

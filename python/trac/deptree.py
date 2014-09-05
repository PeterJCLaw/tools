from collections import Counter
import re
from trac import TracProxy, WrongServer
import xmlrpclib

DEFUALT_TITLE = "\n\nDependencies:\n"
DEFUALT_LIST_PREFIX = " * "

class Ticket(object):
    "A ticket that may have dependencies"

    @staticmethod
    def build_deplist(deps, proxy, list_prefix = DEFUALT_LIST_PREFIX, title = DEFUALT_TITLE):
        d = title
        for ticket_num in deps:
            _, _, _, dep = proxy.ticket.get(ticket_num)

            d += "{prefix}#{num} {summary}\n".format( prefix = list_prefix,
                                                      num = ticket_num,
                                                      summary = dep["summary"] )
        return d

    def __init__(self, num, proxy):
        self.proxy = proxy
        self.num = num
        self.refresh()

    def refresh(self):
        "Refresh with data from trac"
        _, _, _, ticket = self.proxy.ticket.get( self.num )
        desc = self.desc = ticket["description"]
        self.status = ticket["status"]
        self.resolution = ticket["resolution"]
        self.summary = ticket["summary"]
        self.changetime = ticket["changetime"]
        self.component = ticket["component"]
        self.keywords = ticket["keywords"]
        self.milestone = ticket["milestone"]
        self.owner = ticket["owner"]
        self.cc = ticket["cc"]
        self.priority = ticket["priority"]
        self.reporter = ticket["reporter"]
        self.time = ticket["time"]
        self.type = ticket["type"]
        self.version = ticket["version"]

        reg = self._construct_regex()

        self.deps = []

        r = reg.match( desc )
        if r is None:
            "Ticket has no dependencies"
            self.prelude = desc
            self.deptitle = ""
            self.depspace = ""
            self.deplist = ""
            self.postscript = ""
            self.deplist_ends_in_newline = False
            self.list_prefix = ""
            return

        self.prelude = r.group("prelude")
        self.deptitle = r.group("deptitle")
        self.depspace = r.group("depspace")
        self.deplist = r.group("deplist")
        self.postscript = r.group("postscript")

        spacings = Counter()

        for asterisk, ticket_num, desc in  re.findall( r"^(\s*\*\s*)#([0-9]+)\s*(.*)$",
                                                       self.deplist,
                                                       re.MULTILINE | re.IGNORECASE ):
            spacings.update( [asterisk] )
            self.deps.append( int(ticket_num) )

        self.list_prefix = spacings.most_common(1)[0][0]
        self.deplist_ends_in_newline = (self.deplist[-1] == "\n")

    def cleanup(self, dry_run = False, msg = "Synchronise dependency summaries with dependencies (automated edit)"):
        "Clean-up the ticket's description"

        # Rebuild the deplist:
        if len(self.deps) != 0 and self.deptitle == "":
            self.deptitle = DEFUALT_TITLE
            self.list_prefix = DEFUALT_LIST_PREFIX

        title = self.deptitle + self.depspace
        deplist = self.build_deplist(self.deps, self.proxy, self.list_prefix, title)

        if not self.deplist_ends_in_newline:
            deplist = deplist[:-1]

        d = self.prelude + deplist + self.postscript

        if d == self.desc:
            "Description has not changed"
            return False

        if not dry_run:
            self.proxy.ticket.update( self.num, msg,
                                      { "description": d } )

        self.refresh()
        return True

    def _construct_regex(self):
        # Construct a regexp for splitting dependencies from the prelude
        # Prelude section:
        reg = r"(?P<prelude>.*)"

        # Dependencies line
        reg += r"(?P<deptitle>^Dependencies:?$)"

        # Possible newlines between dependencies line and dependency list
        reg += r"(?P<depspace>\s*\n)?"

        # Dependency list:
        reg += r"(?P<deplist>(^\s*\*[^\n]+($\n|\Z))*)"

        # Postscript after the dependency list:
        reg += r"(?P<postscript>.*)"

        return re.compile( reg,
                           re.MULTILINE | re.IGNORECASE | re.DOTALL )

    def __str__(self):
        return "{0}: {1}".format(self.num, self.summary)

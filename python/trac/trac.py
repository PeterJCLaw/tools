
from sr import Config
import sys
from xmlrpclib import ServerProxy

class WrongServer(Exception):
    "The RPC server specified isn't a trac instance"
    pass

class TracProxy(ServerProxy):
    "An XML-RPC proxy for SR Trac"

    select_opts = ['component', 'milestone', 'priority', 'resolution', \
                   'severity', 'status', 'type', 'version']
    freeform = ['cc', 'keywords', 'owner']

    def __init__( self,
                  user = None,
                  password = None,
                  server = None,
                  port = None,
                  anon = False ):
        """Initialise an SR trac object

        Arguments:
        user -- The username.  By default this is looked up in the
                config or the user is prompted for it.
        password -- The password to use.  If left as its default value
                    of None, it may be looked up in the keyring, or
                    the user may be prompted for it.
        server -- The server hostname.  Defaults to that found in the
                  config.
        port -- The HTTPS port of the server.  Defaults to that found
                in the config.
        anon -- Whether to use trac anonymously.
        """

        config = Config()

        if server is None:
            server = config["server"]

        if port is None:
            port = config["https_port"]

        rpc_settings = { "server": server,
                         "port": port }

        if anon:
            rpc_url = "https://{server}:{port}/trac/rpc"
        else:
            rpc_url = "https://{user}:{password}@{server}:{port}/trac/login/rpc"

            user = config.get_user( user )
            rpc_settings["user"] = user
            rpc_settings["password"] = config.get_password( password,
                                                            user = user )

        rpc_url = rpc_url.format( **rpc_settings )

        ServerProxy.__init__(self, rpc_url)

        if "ticket.create" not in self.system.listMethods():
            raise WrongServer

        self._ticket_attributes = {}

    def _get_ticket_attr_values(self, name):
        assert name in self.select_opts
        if name not in self._ticket_attributes:
            self._ticket_attributes[name] = getattr(self.ticket, name).getAll()
        return self._ticket_attributes[name]

    def check_ticket_attrs(self, attrs):
        def check(tpl, value, values):
            if value not in values:
                expecteds = "', '".join(values)
                expecteds = "Expecting one of '{0}'.".format(expecteds)
                raise ValueError(tpl.format(value, expecteds))

        names = self.select_opts + self.freeform

        for name, value in attrs.items():
            check("Unknown attribute '{0}'. {1}", name, names)
            if value is not None and name in self.select_opts:
                values = self._get_ticket_attr_values(name)
                check(name.title() + " '{0}' is not known. {1}", value, values)

    def create_ticket(self, summary, description, attrs):
        self.check_ticket_attrs(attrs)
        return self.ticket.create(summary, description, attrs)

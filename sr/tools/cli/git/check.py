from __future__ import print_function

def command(args):
    import re

    import pygit2


    config = pygit2.Config.get_global_config()

    if not config['user.name'].strip():
        print("You need to tell git who you are.")
        print("Run `git config --global user.name Your Name`.")

    ue = config['user.email'].strip()
    if not ue:
        print("You need to tell git your email address.")
        print("Run `git config --global user.email your@email.com`.")
    elif re.match(r'\S+@\S+\.\S+', ue) is None:
        print("'user.email' doesn't look like an email address.")
        print("Run `git config --global user.email your@email.com`.")

    print("Your git is correctly configured. :)")


def command_no_pygit2(args):
    import sys


    print('Please install pygit2 to use this tool.', file=sys.stderr)
    sys.exit(1)


def add_subparser(subparsers):
    parser = subparsers.add_parser('check-my-git',
                                   help='Checks whether you have git '
                                        'configured sanely.')

    try:
        import pygit2
    except ImportError:
        parser.set_defaults(func=command_no_pygit2)
    else:
        parser.set_defaults(func=command)
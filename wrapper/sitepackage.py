"Functions for checking/adjusting the configuration of the SR python user site package"
import site, os, sys

def check_installed():
    "Check that we're installed, if not, install"
    s = site.getusersitepackages()

    # There should be a symlink
    sym = os.path.join( s, "sr" )
    # to here:
    target = os.path.abspath( os.path.join( os.path.dirname(__file__),
                                            "..", "python" ) )

    if not os.path.exists( s ):
        os.makedirs( s )

    if os.path.exists(sym):
        try:
            cur_target = os.readlink( sym )
            c = os.path.abspath( sym )

            if c == target:
                "Installed, and pointing at the right place"
                return

            # Wrong target directory -- rewrite it
            os.unlink( sym )

        except AttributeError:
            "Python is unable to validate symbolic links on this platform, so try an alternate method"
            import tempfile
            (h, tf) = tempfile.mkstemp( dir = target )
            os.close(h)
            tf = os.path.basename(tf)
            if not os.path.exists(os.path.join( sym, tf )):
                "It's not a link-ish thing, so fake up an error that will be caught below"
                raise OSError
            else:
                "We've shown that it is link-ish"
                return

        except OSError:
            print >>sys.stderr, "Error: %s is not a symlink.  Refusing to continue." % sym
            exit(1)

    print >>sys.stderr, "Installing SR python usersitepackage"

    if not hasattr(os, 'symlink'):
        print >>sys.stderr, "Error: Python is unable to control symbolic links on your platform"
        print >>sys.stderr, "Please create a link from '%s' to '%s'" % ( target, sym )
        exit(1)

    os.symlink( target, sym )

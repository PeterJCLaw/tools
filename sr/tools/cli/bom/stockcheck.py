from __future__ import print_function


def command(args):
    import os
    import sys
    import threading

    import sr.tools.bom.bom as bom
    import sr.tools.bom.parts_db as parts_db
    import sr.tools.bom.schem as schem


    import six.moves.queue as Queue


    NUM_THREADS = 3

    db = parts_db.get_db()
    boards = bom.MultiBoardBom(db)
    boards.load_boards_args(args.arg)

    stock = {}
    n = 0

    for x in boards.stockcheck():
        if not stock.has_key(x[0]):
            stock[x[0]] = []

        stock[x[0]].append(x[1])

        # Show stock checking progress:
        n = n + 1
        sys.stdout.write("\rChecking: %i/%i" % (n, len(boards)))
        sys.stdout.flush()
    print

    if stock.has_key(bom.STOCK_UNKNOWN):
        print("Warning: Cannot check suppliers for these parts:")
        for part in stock[bom.STOCK_UNKNOWN]:
            print("\t- %s %s(%s)" % (part["sr-code"], part["supplier"], part["order-number"]))

    if stock.has_key(bom.STOCK_OUT):
        print("Out of stock:")
        for part in stock[bom.STOCK_OUT]:
            print("\t- %s %s(%s)" % (part["sr-code"], part["supplier"], part["order-number"]))
        sys.exit(1)

    print("All checkable parts are sufficiently in stock.")


def add_subparser(subparsers):
    parser = subparsers.add_parser('stockcheck',
                                   help="Check the stock of boards.")
    parser.add_argument('arg', nargs='+', help="""DIR -N SCHEMATIC1 -M SCHEMATIC2 ...
Where N and M are multipliers for the number of boards.""")
    parser.set_defaults(func=command)
import os
import sys
import transaction

from datetime import date

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    Base,
    Book,
    Order,
    Distributor,
    Binding,
    Publisher,
    ShelfLocation,
    ShippingMethod,
    OrderEntry,
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        distributor = Distributor('Oxford')
        DBSession.add(distributor)
        publishers = [Publisher('Fordham'), Publisher('Oxford'), Publisher('Penguin')]
        DBSession.add_all(publishers)
        bindings = [Binding('Paper'), Binding('Cloth')]
        DBSession.add_all(bindings)
        locations = [ShelfLocation('Fiction'), ShelfLocation('Philosophy')]
        DBSession.add_all(locations)
        shipping = [ShippingMethod('Usual Means'), ShippingMethod('UPS')]
        DBSession.add_all(shipping)
        book = Book('9780199219766',
                    'Great Expectations',
                    'Dickens, Charles',
                    publishers[1],
                    bindings[0],
                    locations[0],
                    )
        DBSession.add(book)
        order = Order('1A1000',
                      date(2012, 1, 1),
                      distributor,
                      shipping[0],
                      'No Backorders'
                      )
        DBSession.add(order)
        order_entry = OrderEntry(order, book, 7)
        DBSession.add(order_entry)

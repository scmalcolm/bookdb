import unittest
import transaction
from datetime import date

from pyramid import testing


def _initTestingDB():
    from sqlalchemy import create_engine
    from bookdb.models import (
        DBSession,
        Base,
        Book,
        Order,
        Distributor,
        Binding,
        Publisher,
        ShelfLocation,
        ShippingMethod,
        OrderEntry
        )
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    DBSession.configure(bind=engine)
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
    return DBSession


class BookModelTests(unittest.TestCase):
    def setUp(self):
        self.session = _initTestingDB()

    def tearDown(self):
        self.session.remove()

    def _getTargetClass(self):
        from bookdb.models import Book
        return Book

    def _makeOne(self,
                 isbn='9780141439600',
                 title='Tale of Two Cities',
                 author='Dickens, Charles',
                 publisher=None,
                 binding=None,
                 location=None):
        from bookdb.models import Publisher, Binding, ShelfLocation
        if publisher is None:
            publisher = self.session.query(Publisher).filter_by(short_name='Penguin').one()
        if binding is None:
            binding = self.session.query(Binding).filter_by(binding='Paper').one()
        if location is None:
            location = self.session.query(ShelfLocation).filter_by(location='Fiction').one()
        return self._getTargetClass()(isbn, title, author, publisher, binding, location)

    def test_constructor(self):
        from bookdb.models import Publisher, Binding, ShelfLocation
        instance = self._makeOne()
        self.assertEqual(instance.isbn13, '9780141439600')
        self.assertEqual(instance.title, 'Tale of Two Cities')
        self.assertEqual(instance.author_name, 'Dickens, Charles')
        self.assertEqual(instance.publisher,
            self.session.query(Publisher).filter_by(short_name='Penguin').one())
        self.assertEqual(instance.binding,
            self.session.query(Binding).filter_by(binding='Paper').one())
        self.assertEqual(instance.shelf_location,
            self.session.query(ShelfLocation).filter_by(location='Fiction').one())

from bookdb.printing import generate_order_pdf
from bookdb.models import Book, Distributor, Order, OrderEntry, ShippingMethod, Binding, Publisher, ShelfLocation

from dateutil.parser import parse as parse_date

_default_filename = 'test.pdf'


def make_test_pdf(filename=_default_filename):
    dummy_order = Order(
        '1A1000',
        parse_date('2012-1-1'),
        Distributor(
            'Warehouse Co.',
            account_number='42',
            fax='555-5543',
            phone='416-555-9876',
            sales_rep='Billy Jo',
            address1='123 Fake Street',
            city="Townville",
            province="Mare Crisium",
            postal_code="ABC123",
            country="The Moon"),
        ShippingMethod("Rocket"),
        'Extra nonsense is free of charge!')
    paperback = Binding('Paper')
    penguin = Publisher('Penguin')
    location = ShelfLocation('Dreamspace')
    for x in xrange(10, 35):
            OrderEntry(
            dummy_order,
            Book(
                '97811122233' + str(x),
                'BOOK' + str(x),
                penguin,
                paperback,
                location,
                [('Seneca',), ('Brown', 'Dan')]),
            x)
    OrderEntry(
        dummy_order,
        Book(
            '9781112223399',
            'AWESOME',
            penguin,
            paperback,
            location,
            [('Seneca',), ('Brown', 'Dan')]),
        9)
    generate_order_pdf(dummy_order, filename)

if __name__ == '__main__':
    make_test_pdf()

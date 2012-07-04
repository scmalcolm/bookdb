from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    Date,
    ForeignKey,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    )

from zope.sqlalchemy import ZopeTransactionExtension

from pyramid.security import (
    Allow,
    Everyone,
    )

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Book(Base):
    __tablename__ = 'books'
    book_id = Column(Integer, primary_key=True)
    binding_id = Column(Integer, ForeignKey('bindings.binding_id'))
    location_id = Column(Integer, ForeignKey('shelf_locations.location_id'))
    publisher_id = Column(Integer, ForeignKey('publishers.publisher_id'))
    isbn13 = Column(String(13), unique=True)
    title = Column(String)
    author_name = Column(String)  # use format 'last1, first1; last2, first2; ...'
    publisher = relationship("Publisher")
    shelf_location = relationship("ShelfLocation")
    binding = relationship("Binding")
    authors = relationship("Author", back_populates="book", cascade="all, delete-orphan")

    def __init__(self, isbn13, title, publisher, binding, shelf_location, authors=[]):
        self.isbn13 = isbn13
        self.title = title
        self.publisher = publisher
        self.binding = binding
        self.shelf_location = shelf_location
        self.authors = [Author(first, last) for first, last in authors]

    def author_lastname(self):
        return self.authors[0].lastname

    def author_string(self):
        return '; '.join([str(a) for a in self.authors])


class Author(Base):
    __tablename__ = 'authors'
    author_id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.book_id'))
    lastname = Column(String)
    firstname = Column(String)
    comment = Column(String)
    book = relationship("Book", back_populates="authors")

    @classmethod
    def parse_author_string(string):
        return [(a[1], a[0]) for a in map(lambda(x): x.split(', '), string.split('; '))]

    @classmethod
    def create_author_string(authors):
        return '; '.join(map(lambda(x): ', '.join(x.lastname, x.firstname), authors))

    def __init__(self, lastname, firstname, comment=None):
        self.lastname = lastname
        self.firstname = firstname
        self.comment = comment

    def __repr__(self):
        return ', '.join([self.lastname, self.firstname])


class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True)
    distributor_id = Column(Integer, ForeignKey('distributors.distributor_id'))
    shipping_id = Column(Integer, ForeignKey('shipping_methods.shipping_id'))
    po = Column(String, unique=True)
    date = Column(Date)
    comment = Column(Text)
    order_entries = relationship("OrderEntry", back_populates="order", cascade="all, delete-orphan")
    distributor = relationship("Distributor")
    shipping_method = relationship("ShippingMethod")

    def __init__(self, po, date, distributor, shipping_method, comment):
        self.po = po
        self.date = date
        self.distributor = distributor
        self.shipping_method = shipping_method
        self.comment = comment


class Distributor(Base):
    __tablename__ = 'distributors'
    distributor_id = Column(Integer, primary_key=True)
    short_name = Column(String, unique=True, nullable=False)
    full_name = Column(String, unique=True, nullable=False)
    account_number = Column(String)
    sales_rep = Column(String)
    phone = Column(String)
    fax = Column(String)
    email = Column(String)
    address1 = Column(String)
    address2 = Column(String)
    city = Column(String)
    province = Column(String)
    postal_code = Column(String)
    country = Column(String)

    def __init__(self, short_name, full_name=None):
        self.short_name = short_name
        if full_name is None:
            self.full_name = short_name
        else:
            self.full_name = full_name

    def __repr__(self):
        return self.short_name

    def mailing_address(self):
        address_lines = [self.full_name]
        if self.address1 is not None:
            address_lines.append(self.address1)
        if self.address2 is not None:
            address_lines.append(self.address2)
        city_line = ' '.join([x for x in (self.city, self.province, self.postal_code) if x is not None])
        if city_line is not None and city_line != '':
            address_lines.append(city_line)
        if self.country is not None and self.country != 'Canada':
            address_lines.append(self.country)
        return '\n'.join(address_lines)


class Publisher(Base):
    __tablename__ = 'publishers'
    publisher_id = Column(Integer, primary_key=True)
    short_name = Column(Text, unique=True)
    full_name = Column(Text)

    def __init__(self, short_name, full_name=None):
        self.short_name = short_name
        if full_name is None:
            self.full_name = short_name
        else:
            self.full_name = full_name

    def __repr__(self):
        return self.short_name


class ShelfLocation(Base):
    __tablename__ = 'shelf_locations'
    location_id = Column(Integer, primary_key=True)
    location = Column(Text, unique=True)

    def __init__(self, location):
        self.location = location

    def __repr__(self):
        return self.location


class Binding(Base):
    __tablename__ = 'bindings'
    binding_id = Column(Integer, primary_key=True)
    binding = Column(Text, unique=True)

    def __init__(self, binding):
        self.binding = binding

    def __repr__(self):
        return self.binding


class ShippingMethod(Base):
    __tablename__ = 'shipping_methods'
    shipping_id = Column(Integer, primary_key=True)
    shipping_method = Column(Text)

    def __init__(self, shipping_method):
        self.shipping_method = shipping_method

    def __repr__(self):
        return self.shipping_method


class OrderEntry(Base):
    __tablename__ = 'order_entries'
    order_id = Column(Integer, ForeignKey('orders.order_id'), primary_key=True)
    book_id = Column(Integer, ForeignKey('books.book_id'), primary_key=True)
    quantity = Column(Integer)
    order = relationship("Order", back_populates="order_entries")
    book = relationship("Book")

    def __init__(self, order, book, quantity):
        self.order = order
        self.book = book
        self.quantity = quantity


class RootFactory(object):
    __acl__ = [(Allow, Everyone, 'view'),
               (Allow, 'group:editors', 'edit')]

    def __init__(self, request):
        pass

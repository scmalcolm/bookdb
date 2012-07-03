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
    id = Column(Integer, primary_key=True)
    binding_id = Column(Integer, ForeignKey('bindings.id'))
    location_id = Column(Integer, ForeignKey('shelf_locations.id'))
    publisher_id = Column(Integer, ForeignKey('publishers.id'))
    isbn13 = Column(Text, unique=True)
    title = Column(Text)
    author_name = Column(Text)  # use format 'last1, first1; last2, first2; ...'
    publisher = relationship("Publisher")
    shelf_location = relationship("ShelfLocation")
    binding = relationship("Binding")

    def __init__(self, isbn13, title, authors, publisher, binding, shelf_location):
        self.isbn13 = isbn13
        self.title = title
        self.author_name = authors
        self.publisher = publisher
        self.binding = binding
        self.shelf_location = shelf_location

    def author_lastname(self):
        authors = self.author_name.split(';')
        author = authors[0].split(',')
        return author[0]


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    distributor_id = Column(Integer, ForeignKey('distributors.id'))
    shipping_id = Column(Integer, ForeignKey('shipping_methods.id'))
    po = Column(Text, unique=True)
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
    id = Column(Integer, primary_key=True)
    short_name = Column(Text, unique=True, nullable=False)
    full_name = Column(Text, unique=True, nullable=False)
    account_number = Column(Text)
    sales_rep = Column(Text)
    phone = Column(Text)
    fax = Column(Text)
    email = Column(Text)
    street_address = Column(String)
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
        if self.street_address is not None:
            address_lines.append(self.street_address.split('\n'))
        city_line = ' '.join([x for x in (self.city, self.province, self.postal_code) if x is not None])
        if city_line is not None and city_line != '':
            address_lines.append(city_line)
        if self.country is not None and self.country != 'Canada':
            address_lines.append(self.country)
        return '\n'.join(address_lines)


class Publisher(Base):
    __tablename__ = 'publishers'
    id = Column(Integer, primary_key=True)
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
    id = Column(Integer, primary_key=True)
    location = Column(Text, unique=True)

    def __init__(self, location):
        self.location = location

    def __repr__(self):
        return self.location


class Binding(Base):
    __tablename__ = 'bindings'
    id = Column(Integer, primary_key=True)
    binding = Column(Text, unique=True)

    def __init__(self, binding):
        self.binding = binding

    def __repr__(self):
        return self.binding


class ShippingMethod(Base):
    __tablename__ = 'shipping_methods'
    id = Column(Integer, primary_key=True)
    shipping_method = Column(Text)

    def __init__(self, shipping_method):
        self.shipping_method = shipping_method

    def __repr__(self):
        return self.shipping_method


class OrderEntry(Base):
    __tablename__ = 'order_entries'
    order_id = Column(Integer, ForeignKey('orders.id'), primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), primary_key=True)
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

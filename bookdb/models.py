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
    exc as sqlexceptions,
    )

from zope.sqlalchemy import ZopeTransactionExtension

from pyramid.security import (
    Allow,
    Everyone,
    )

import re

ISBN13_REGEX = re.compile("^\d{13}$")

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


def valid_isbn13(isbn13):
    if ISBN13_REGEX.match(isbn13) is None:
        return False
    total = sum([int(num) * weight for num, weight in zip(isbn13, (1, 3) * 6)])
    ck = (10 - (total % 10)) % 10
    return ck == int(isbn13[-1])


class Book(Base):
    __tablename__ = 'books'
    book_id = Column(Integer, primary_key=True)
    binding_id = Column(Integer, ForeignKey('bindings.binding_id'), nullable=False)
    location_id = Column(Integer, ForeignKey('shelf_locations.location_id'), nullable=False)
    publisher_id = Column(Integer, ForeignKey('publishers.publisher_id'), nullable=False)
    isbn13 = Column(String(13), unique=True)
    title = Column(String)
    author_name = Column(String)  # use format 'last1, first1; last2, first2; ...'
    publisher = relationship("Publisher")
    shelf_location = relationship("ShelfLocation")
    binding = relationship("Binding")
    authors = relationship("Author", back_populates="book", cascade="all, delete-orphan")

    def __init__(self, isbn13, title, publisher, binding, shelf_location, authors=[]):
        self.isbn13 = isbn13
        self.title = title.upper()
        self.publisher = publisher
        self.binding = binding
        self.shelf_location = shelf_location
        self.authors = authors

    def author_lastname(self):
        if self.authors == []:
            return ''
        else:
            return self.authors[0].lastname

    def author_string(self):
        return '; '.join([unicode(a) for a in self.authors])

    @classmethod
    def get(cls, isbn13, default=None):
        try:
            result = DBSession.query(Book).filter_by(isbn13=isbn13).one()
        except sqlexceptions.NoResultFound:
            result = default
        return result

    @classmethod
    def list(cls):
        return DBSession.query(Book).order_by(Book.isbn13).all()


class Author(Base):
    __tablename__ = 'authors'
    author_id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.book_id'), nullable=False)
    lastname = Column(String)
    firstname = Column(String)
    book = relationship("Book", back_populates="authors")

    @classmethod
    def parse_author_string(cls, string):
        result = []
        authors = string.split('; ')
        for a in authors:
            if len(a) > 0:
                try:
                    (lname, fname) = a.split(', ')
                except ValueError:
                    lname = a
                    fname = None
                result.append(Author(lname, fname))
        return result

    @classmethod
    def create_author_string(cls, authors):
        return u'; '.join(map(lambda x: ', '.join(x.lastname, x.firstname), authors))

    def __init__(self, lastname, firstname=None):
        self.lastname = lastname
        self.firstname = firstname

    def __repr__(self):
        if self.firstname is not None:
            return ', '.join([self.lastname, self.firstname])
        else:
            return self.lastname


class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True)
    distributor_id = Column(Integer, ForeignKey('distributors.distributor_id'), nullable=False)
    shipping_id = Column(Integer, ForeignKey('shipping_methods.shipping_id'), nullable=False)
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

    @classmethod
    def get(cls, po, default=None):
        try:
            result = DBSession.query(Order).filter_by(po=po).one()
        except sqlexceptions.NoResultFound:
            result = default
        return result

    @classmethod
    def list(cls):
        return DBSession.query(Order).order_by(Order.po).all()


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

    def __init__(self, short_name, full_name=None, account_number=None, sales_rep=None, phone=None,
        fax=None, email=None, address1=None, address2=None, city=None, province=None, postal_code=None, country=None):
        self.short_name = short_name
        if full_name is None:
            self.full_name = short_name
        else:
            self.full_name = full_name
        self.account_number = account_number
        self.sales_rep = sales_rep
        self.phone = phone
        self.fax = fax
        self.email = email
        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.province = province
        self.postal_code = postal_code
        self.country = country

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

    @classmethod
    def get(cls, name, default=None):
        try:
            result = DBSession.query(Distributor).filter_by(short_name=name).one()
        except sqlexceptions.NoResultFound:
            result = default
        return result

    @classmethod
    def list(cls):
        return DBSession.query(Distributor).order_by(Distributor.short_name).all()


class Publisher(Base):
    __tablename__ = 'publishers'
    publisher_id = Column(Integer, primary_key=True)
    short_name = Column(Text, unique=True, nullable=False)
    full_name = Column(Text)

    def __init__(self, short_name, full_name=None):
        self.short_name = short_name
        if full_name is None:
            self.full_name = short_name
        else:
            self.full_name = full_name

    def __repr__(self):
        return self.short_name

    @classmethod
    def get(cls, name, default=None):
        try:
            result = DBSession.query(Publisher).filter_by(short_name=name).one()
        except sqlexceptions.NoResultFound:
            result = default
        return result

    @classmethod
    def list(cls):
        return DBSession.query(Publisher).order_by(Publisher.short_name).all()


class ShelfLocation(Base):
    __tablename__ = 'shelf_locations'
    location_id = Column(Integer, primary_key=True)
    location = Column(Text, unique=True, nullable=False)

    def __init__(self, location):
        self.location = location

    def __repr__(self):
        return self.location

    @classmethod
    def get(cls, location, default=None):
        try:
            result = DBSession.query(ShelfLocation).filter_by(location=location).one()
        except sqlexceptions.NoResultFound:
            result = default
        return result

    @classmethod
    def list(cls):
        return DBSession.query(ShelfLocation).order_by(ShelfLocation.location).all()


class Binding(Base):
    __tablename__ = 'bindings'
    binding_id = Column(Integer, primary_key=True)
    binding = Column(Text, unique=True, nullable=False)

    def __init__(self, binding):
        self.binding = binding

    def __repr__(self):
        return self.binding

    @classmethod
    def get(cls, binding, default=None):
        try:
            result = DBSession.query(Binding).filter_by(binding=binding).one()
        except sqlexceptions.NoResultFound:
            result = default
        return result

    @classmethod
    def list(cls):
        return DBSession.query(Binding).order_by(Binding.binding).all()


class ShippingMethod(Base):
    __tablename__ = 'shipping_methods'
    shipping_id = Column(Integer, primary_key=True)
    shipping_method = Column(Text, unique=True, nullable=False)

    def __init__(self, shipping_method):
        self.shipping_method = shipping_method

    def __repr__(self):
        return self.shipping_method

    @classmethod
    def get(cls, method, default=None):
        try:
            result = DBSession.query(ShippingMethod).filter_by(shipping_method=method).one()
        except sqlexceptions.NoResultFound:
            result = default
        return result

    @classmethod
    def list(cls):
        return DBSession.query(ShippingMethod).order_by(ShippingMethod.shipping_method).all()


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

    @classmethod
    def get(cls, po, isbn13, default=None):
        try:
            order = DBSession.query(Order).filter_by(po=po).one()
            book = DBSession.query(Book).filter_by(isbn13=isbn13).one()
            result = DBSession.query(OrderEntry).filter_by(order=order, book=book).one()
        except sqlexceptions.NoResultFound:
            result = default
        return result


class RootFactory(object):
    __acl__ = [(Allow, Everyone, 'view'),
               (Allow, 'group:editors', 'edit')]

    def __init__(self, request):
        pass

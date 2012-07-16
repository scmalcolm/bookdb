from dateutil.parser import parse as parse_date

from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    )
from pyramid.view import (
    view_config,
    forbidden_view_config,
    )
from pyramid.renderers import get_renderer

from pyramid.security import (
    remember,
    forget,
    authenticated_userid
    )

from .models import (
    DBSession,
    Book,
    ShelfLocation,
    Binding,
    Publisher,
    Order,
    OrderEntry,
    ShippingMethod,
    Distributor,
    Author,
    )

from .printing import generate_order_pdf

from .security import USERS


@view_config(route_name='front_page', renderer='templates/front_page.pt')
def front_page(request):
    return dict(theme=Theme(request),
                )


@view_config(route_name='book_view', renderer='templates/book_view.pt')
def book_view(request):
    isbn13 = request.matchdict['isbn13']
    book = DBSession.query(Book).filter_by(isbn13=isbn13).first()
    if book is None:
        return HTTPNotFound('No such book')
    edit_url = request.route_url('book_edit', isbn13=isbn13)
    return dict(theme=Theme(request),
                book=book,
                edit_url=edit_url,
                )


@view_config(route_name='book_add', renderer='templates/book_edit.pt', permission='edit')
def book_add(request):
    if 'form.submitted' in request.params:
        isbn13 = request.params['isbn13']
        title = request.params['title']
        author_string = request.params['author_string']
        publisher = DBSession.query(Publisher).filter_by(
                            short_name=request.params['publisher']).one()
        binding = DBSession.query(Binding).filter_by(
                            binding=request.params['binding']).one()
        shelf_location = DBSession.query(ShelfLocation).filter_by(
                            location=request.params['shelf_location']).one()
        if author_string == '':
            authors = []
        else:
            authors = Author.parse_author_string(author_string)
        # TODO: validate data
        new_book = Book(isbn13, title, publisher, binding, shelf_location, authors=authors)
        DBSession.add(new_book)
        return HTTPFound(location=request.route_url('book_add'))
    save_url = request.route_url('book_add')
    book = Book('', '', '', '', '', [])
    bindings = DBSession.query(Binding).all()
    locations = DBSession.query(ShelfLocation).all()
    publishers = DBSession.query(Publisher).all()
    return dict(theme=Theme(request),
                book=book,
                save_url=save_url,
                bindings=bindings,
                locations=locations,
                publishers=publishers,
                )


@view_config(route_name='book_edit', renderer='templates/book_edit.pt', permission='edit')
def book_edit(request):
    isbn13 = request.matchdict['isbn13']
    book = DBSession.query(Book).filter_by(isbn13=isbn13).one()
    if 'form.submitted' in request.params:
        # TODO: Validate data before accepting it.
        book.isbn13 = request.params['isbn13']
        book.title = request.params['title']
        author_string = request.params['author_string']
        if author_string == '':
            book.authors = []
        else:
            book.authors = Author.parse_author_string(author_string)
        book.publisher = DBSession.query(Publisher).filter_by(
                            short_name=request.params['publisher']).one()
        book.binding = DBSession.query(Binding).filter_by(
                            binding=request.params['binding']).one()
        book.shelf_location = DBSession.query(ShelfLocation).filter_by(
                            location=request.params['shelf_location']).one()
        DBSession.add(book)
        return HTTPFound(location=request.route_url('book_view', isbn13=book.isbn13))
    bindings = DBSession.query(Binding).all()
    locations = DBSession.query(ShelfLocation).all()
    publishers = DBSession.query(Publisher).all()
    return dict(theme=Theme(request),
                book=book,
                save_url=request.route_url('book_edit', isbn13=isbn13),
                bindings=bindings,
                locations=locations,
                publishers=publishers,
                )


@view_config(route_name='book_delete', renderer='templates/book_delete.pt', permission='edit')
def book_delete(request):
    isbn13 = request.matchdict['isbn13']
    book = DBSession.query(Book).filter_by(isbn13=isbn13).one()
    if 'form.submitted' in request.params:
        DBSession.delete(book)
        return HTTPFound(location=request.route_url('book_list'))
    return dict(theme=Theme(request),
                book=book,
                delete_url=request.route_url('book_delete', isbn13=isbn13),
                )


@view_config(route_name='book_list', renderer='templates/book_list.pt')
def book_list(request):
    books = DBSession.query(Book).all()
    return dict(theme=Theme(request),
                books=books,
                book_url=lambda isbn13: request.route_url('book_view', isbn13=isbn13)
                )


@view_config(route_name='order_list', renderer='templates/order_list.pt')
def order_list(request):
    orders = DBSession.query(Order).all()
    return dict(theme=Theme(request),
                orders=orders,
                order_url=lambda po: request.route_url('order_view', po=po)
                )


@view_config(route_name='order_view', renderer='templates/order_view.pt')
def order_view(request):
    po = request.matchdict['po']
    order = DBSession.query(Order).filter_by(po=po).one()
    return dict(theme=Theme(request),
                order=order,
                edit_url=request.route_url('order_edit', po=po),
                pdf_url=request.route_url('order_pdf', po=po),
                )


@view_config(route_name='order_pdf')
def order_pdf(request):
    po = request.matchdict['po']
    order = DBSession.query(Order).filter_by(po=po).one()
    filename = '/Users/bmbr/Orders/{}.pdf'.format(po)
    generate_order_pdf(order, filename)
    return HTTPFound(location=request.route_url('order_view', po=po))


@view_config(route_name='order_add', renderer='templates/order_add.pt', permission='edit')
def order_add(request):
    if 'form.submitted' in request.params:
        po = request.params['po']
        distributor = DBSession.query(Distributor).filter_by(
                            short_name=request.params['distributor']).one()
        shipping_method = DBSession.query(ShippingMethod).filter_by(
                            shipping_method=request.params['shipping_method']).one()
        date = parse_date(request.params['order_date'])
        comment = request.params['comment']
        new_order = Order(po, date, distributor, shipping_method, comment)
        DBSession.add(new_order)
        return HTTPFound(request.route_url('order_edit', po=po))
    save_url = request.route_url('order_add')
    shipping_methods = DBSession.query(ShippingMethod).all()
    distributors = DBSession.query(Distributor).all()
    return dict(theme=Theme(request),
                save_url=save_url,
                shipping_methods=shipping_methods,
                distributors=distributors,
                )


@view_config(route_name='order_edit', renderer='templates/order_edit.pt', permission='edit')
def order_edit(request):
    po = request.matchdict['po']
    order = DBSession.query(Order).filter_by(po=po).one()
    message = ''
    if 'header.submitted' in request.params:
        po = request.params['po']
        order_date = parse_date(request.params['order_date'])
        distributor = DBSession.query(Distributor).filter_by(
                        short_name=request.params['distributor']).one()
        shipping_method = DBSession.query(ShippingMethod).filter_by(
                        shipping_method=request.params['shipping_method']).one()
        comment = request.params['comment']
        # TODO: validate new header data
        order.po = po
        order.order_date = order_date
        order.distributor = distributor
        order.shipping_method = shipping_method
        order.comment = comment
        DBSession.add(order)
        return HTTPFound(location=request.route_url('order_list'))
    elif 'new_entry.submitted' in request.params:
        try:
            book = DBSession.query(Book).filter_by(isbn13=request.params['isbn13']).one()
        except:
            book = None
        try:
            quantity = int(request.params['quantity'])
            assert quantity > 0
        except:
            quantity = None
        if book is None:
            message = "Invalid ISBN ({})! No such book".format(request.params['isbn13'])
        elif quantity is None:
            message = "Invalid quantity ({})! Must be a positive integer.".format(quantity)
        else:
            DBSession.add(OrderEntry(order, book, quantity))
            return HTTPFound(location=request.route_url('order_edit', po=po))
    shipping_methods = DBSession.query(ShippingMethod).all()
    distributors = DBSession.query(Distributor).all()
    return dict(theme=Theme(request),
                order=order,
                message=message,
                save_url=request.route_url('order_edit', po=po),
                shipping_methods=shipping_methods,
                distributors=distributors,
                delete_entry_pattern=request.application_url + "/order/{po}/delete_entry/{isbn13}",
                )


@view_config(route_name='order_delete', renderer='templates/order_delete.pt', permission='edit')
def order_delete(request):
    po = request.matchdict['po']
    order = DBSession.query(Order).filter_by(po=po).one()
    if 'form.submitted' in request.params:
        DBSession.delete(order)
        return HTTPFound(location=request.route_url('order_list'))
    return dict(theme=Theme(request),
                order=order,
                delete_url=request.route_url('order_delete', po=po),
                )


@view_config(route_name='order_entry_delete', permission='edit')
def order_entry_delete(request):
    po = request.matchdict['po']
    isbn13 = request.matchdict['isbn13']
    order = DBSession.query(Order).filter_by(po=po).one()
    book = DBSession.query(Book).filter_by(isbn13=isbn13).one()
    order_entry = DBSession.query(OrderEntry).filter_by(order=order, book=book).one()
    DBSession.delete(order_entry)
    return HTTPFound(location=request.route_url('order_edit', po=po))


@view_config(route_name='distributor_list', renderer='templates/distributor_list.pt')
def distributor_list(request):
    distributors = DBSession.query(Distributor).all()
    return dict(theme=Theme(request),
                distributors=distributors,
                distributor_url=lambda name: request.route_url('distributor_view', short_name=name),
                )


@view_config(route_name='distributor_view', renderer='templates/distributor_view.pt')
def distributor_view(request):
    name = request.matchdict['short_name']
    distributor = DBSession.query(Distributor).filter_by(short_name=name).one()
    shared_template = get_renderer('templates/shared.pt').implementation()
    return dict(theme=Theme(request),
                shared=shared_template,
                distributor=distributor,
                edit_url=request.route_url('distributor_edit', short_name=name),
                )


@view_config(route_name='distributor_add', renderer='templates/distributor_edit.pt', permission='edit')
def distributor_add(request):
    if 'form.submitted' in request.params:
        short_name = request.params['short_name']
        full_name = request.params['full_name']
        account_number = request.params['account_number']
        sales_rep = request.params['sales_rep']
        phone = request.params['phone']
        fax = request.params['fax']
        email = request.params['email']
        address1 = request.params['address1']
        address2 = request.params['address2']
        city = request.params['city']
        province = request.params['province']
        postal_code = request.params['postal_code']
        country = request.params['country']
        distributor = Distributor(short_name, full_name, account_number, sales_rep, phone,
            fax, email, address1, address2, city, province, postal_code, country)
        DBSession.add(distributor)
        return HTTPFound(request.route_url('distributor_view', short_name=short_name))
    distributor = Distributor('')
    return dict(theme=Theme(request),
                distributor=distributor,
                save_url=request.route_url('distributor_add'),
                )


@view_config(route_name='distributor_edit', renderer='templates/distributor_edit.pt', permission='edit')
def distributor_edit(request):
    name = request.matchdict['short_name']
    distributor = DBSession.query(Distributor).filter_by(short_name=name).one()
    if 'form.submitted' in request.params:
        distributor.short_name = request.params['short_name']
        distributor.full_name = request.params['full_name']
        distributor.account_number = request.params['account_number']
        distributor.sales_rep = request.params['sales_rep']
        distributor.phone = request.params['phone']
        distributor.fax = request.params['fax']
        distributor.email = request.params['email']
        distributor.address1 = request.params['address1']
        distributor.address2 = request.params['address2']
        distributor.city = request.params['city']
        distributor.province = request.params['province']
        distributor.postal_code = request.params['postal_code']
        distributor.country = request.params['country']
        return HTTPFound(request.route_url('distributor_list'))
    return dict(theme=Theme(request),
                distributor=distributor,
                save_url=request.route_url('distributor_edit', short_name=name),
                )


@view_config(route_name='distributor_delete', permission='edit')
def distributor_delete(request):
    name = request.matchdict['short_name']
    distributor = DBSession.query(Distributor).filter_by(short_name=name).one()
    DBSession.delete(distributor)
    return HTTPFound(request.route_url('distributor_list'))


@view_config(route_name='publisher_list', renderer='templates/publisher_list.pt')
def publisher_list(request):
    publishers = DBSession.query(Publisher).all()
    return dict(theme=Theme(request),
                publishers=publishers,
                edit_url=lambda pub: request.route_url('publisher_edit', short_name=pub.short_name),
                )


@view_config(route_name='publisher_edit', renderer='templates/publisher_edit.pt', permission='edit')
def publisher_edit(request):
    name = request.matchdict['short_name']
    publisher = DBSession.query(Publisher).filter_by(short_name=name).one()
    if 'form.submitted' in request.params:
        publisher.short_name = request.params['short_name']
        publisher.full_name = request.params['full_name']
        return HTTPFound(request.route_url('publisher_list'))
    elif 'form.delete' in request.params:
        DBSession.delete(publisher)
        return HTTPFound(request.route_url('publisher_list'))
    return dict(theme=Theme(request),
                publisher=publisher,
                save_url=request.route_url('publisher_edit', short_name=name)
                )


@view_config(route_name='publisher_add', renderer='templates/publisher_edit.pt', permission='edit')
def publisher_add(request):
    if 'form.submitted' in request.params:
        short_name = request.params['short_name']
        full_name = request.params['full_name']
        if full_name == '':
            full_name = short_name
        publisher = Publisher(short_name, full_name)
        DBSession.add(publisher)
        return HTTPFound(request.route_url('publisher_list'))
    return dict(theme=Theme(request),
                publisher=Publisher('', ''),
                save_url=request.route_url('publisher_add'),
                )


@view_config(route_name='login', renderer='templates/login.pt')
@forbidden_view_config(renderer='templates/login.pt')
def login(request):
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        login = request.params['login']
        password = request.params['password']
        if USERS.get(login) == password:
            headers = remember(request, login)
            return HTTPFound(location=came_from, headers=headers)
        message = 'Failed login'
    return dict(theme=Theme(request, logged_in=False),
                message=message,
                url=request.application_url + '/login',
                came_from=came_from,
                login=login,
                password=password,
                )


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.route_url('front_page'), headers=headers)


class Theme(object):
    def __init__(self, request, logged_in=None):
        self.request = request
        if logged_in is None:
            self._logged_in = None
        else:
            self._logged_in = logged_in

    @property
    def logged_in(self):
        if self._logged_in is None:
            return authenticated_userid(self.request)
        else:
            return self._logged_in

    @property
    def develop(self):
        return self.request.registry.settings['develop']

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
    book = Book.get(isbn13)
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
        publisher = Publisher.get(request.params['publisher'])
        binding = Binding.get(request.params['binding'])
        shelf_location = ShelfLocation.get(request.params['shelf_location'])
        authors = Author.parse_author_string(author_string)
        # TODO: validate data
        new_book = Book(isbn13, title, publisher, binding, shelf_location, authors=authors)
        DBSession.add(new_book)
        return HTTPFound(location=request.route_url('book_add'))
    book = Book('', '', '', '', '', [])
    return dict(theme=Theme(request),
                book=book,
                save_url=request.route_url('book_add'),
                bindings=Binding.list(),
                locations=ShelfLocation.list(),
                publishers=Publisher.list(),
                )


@view_config(route_name='book_edit', renderer='templates/book_edit.pt', permission='edit')
def book_edit(request):
    isbn13 = request.matchdict['isbn13']
    book = Book.get(isbn13=isbn13)
    if 'form.submitted' in request.params:
        # TODO: Validate data before accepting it.
        book.isbn13 = request.params['isbn13']
        book.title = request.params['title']
        author_string = request.params['author_string']
        book.publisher = Publisher.get(request.params['publisher'])
        book.binding = Binding.get(request.params['binding'])
        book.shelf_location = ShelfLocation.get(request.params['shelf_location'])
        book.authors = Author.parse_author_string(author_string)
        return HTTPFound(location=request.route_url('book_view', isbn13=book.isbn13))
    return dict(theme=Theme(request),
                book=book,
                save_url=request.route_url('book_edit', isbn13=isbn13),
                bindings=Binding.list(),
                locations=ShelfLocation.list(),
                publishers=Publisher.list(),
                )


@view_config(route_name='book_delete', renderer='templates/book_delete.pt', permission='edit')
def book_delete(request):
    isbn13 = request.matchdict['isbn13']
    book = Book.get(isbn13)
    if 'form.submitted' in request.params:
        DBSession.delete(book)
        return HTTPFound(location=request.route_url('book_list'))
    return dict(theme=Theme(request),
                book=book,
                delete_url=request.route_url('book_delete', isbn13=isbn13),
                )


@view_config(route_name='book_list', renderer='templates/book_list.pt')
def book_list(request):
    books = Book.list()
    return dict(theme=Theme(request),
                books=books,
                book_url=lambda isbn13: request.route_url('book_view', isbn13=isbn13)
                )


@view_config(route_name='order_list', renderer='templates/order_list.pt')
def order_list(request):
    orders = Order.list()
    return dict(theme=Theme(request),
                orders=orders,
                order_url=lambda po: request.route_url('order_view', po=po)
                )


@view_config(route_name='order_view', renderer='templates/order_view.pt')
def order_view(request):
    po = request.matchdict['po']
    order = Order.get(po)
    return dict(theme=Theme(request),
                order=order,
                edit_url=request.route_url('order_edit', po=po),
                pdf_url=request.route_url('order_pdf', po=po),
                )


@view_config(route_name='order_pdf')
def order_pdf(request):
    po = request.matchdict['po']
    order = Order.get(po)
    filename = '/Users/bmbr/Orders/{}.pdf'.format(po)
    generate_order_pdf(order, filename)
    return HTTPFound(location=request.route_url('order_view', po=po))


@view_config(route_name='order_add', renderer='templates/order_add.pt', permission='edit')
def order_add(request):
    if 'form.submitted' in request.params:
        po = request.params['po']
        distributor = Distributor.get(request.params['distributor'])
        shipping_method = ShippingMethod.get(request.params['shipping_method'])
        date = parse_date(request.params['order_date'])
        comment = request.params['comment']
        new_order = Order(po, date, distributor, shipping_method, comment)
        DBSession.add(new_order)
        return HTTPFound(request.route_url('order_edit', po=po))
    save_url = request.route_url('order_add')
    return dict(theme=Theme(request),
                save_url=save_url,
                shipping_methods=ShippingMethod.list(),
                distributors=Distributor.list(),
                )


@view_config(route_name='order_edit', renderer='templates/order_edit.pt', permission='edit')
def order_edit(request):
    po = request.matchdict['po']
    order = Order.get(po)
    message = ''
    if 'header.submitted' in request.params:
        po = request.params['po']
        order_date = parse_date(request.params['order_date'])
        distributor = Distributor.get(request.params['distributor'])
        shipping_method = ShippingMethod.get(request.params['shipping_method'])
        comment = request.params['comment']
        # TODO: validate new header data
        order.po = po
        order.order_date = order_date
        order.distributor = distributor
        order.shipping_method = shipping_method
        order.comment = comment
        return HTTPFound(location=request.route_url('order_list'))
    elif 'new_entry.submitted' in request.params:
        isbn13 = request.params['isbn13']
        book = Book.get(isbn13)
        try:
            quantity = int(request.params['quantity'])
            assert quantity > 0
        except (AssertionError, ValueError):
            quantity = None
        if book is None:
            # TODO: prompt for insertion of new book
            message = "No book with ISBN: {}!".format(isbn13)
        elif quantity is None:
            message = "Quantity ({}) must be a positive integer!".format(quantity)
        else:
            DBSession.add(OrderEntry(order, book, quantity))
            return HTTPFound(location=request.route_url('order_edit', po=po))
    return dict(theme=Theme(request),
                order=order,
                message=message,
                save_url=request.route_url('order_edit', po=po),
                shipping_methods=ShippingMethod.list(),
                distributors=Distributor.list(),
                delete_entry_pattern=request.application_url + "/order/{po}/delete_entry/{isbn13}",
                )


@view_config(route_name='order_delete', renderer='templates/order_delete.pt', permission='edit')
def order_delete(request):
    po = request.matchdict['po']
    order = Order.get(po)
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
    order_entry = OrderEntry.get(po, isbn13)
    DBSession.delete(order_entry)
    return HTTPFound(location=request.route_url('order_edit', po=po))


@view_config(route_name='distributor_list', renderer='templates/distributor_list.pt')
def distributor_list(request):
    distributors = Distributor.list()
    return dict(theme=Theme(request),
                distributors=distributors,
                distributor_url=lambda name: request.route_url('distributor_view', short_name=name),
                )


@view_config(route_name='distributor_view', renderer='templates/distributor_view.pt')
def distributor_view(request):
    name = request.matchdict['short_name']
    distributor = Distributor.get(name)
    return dict(theme=Theme(request),
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
    distributor = Distributor.get(name)
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
    distributor = Distributor.get(name)
    DBSession.delete(distributor)
    return HTTPFound(request.route_url('distributor_list'))


@view_config(route_name='publisher_list', renderer='templates/publisher_list.pt')
def publisher_list(request):
    publishers = Publisher.list()
    return dict(theme=Theme(request),
                publishers=publishers,
                edit_url=lambda pub: request.route_url('publisher_edit', short_name=pub.short_name),
                )


@view_config(route_name='publisher_edit', renderer='templates/publisher_edit.pt', permission='edit')
def publisher_edit(request):
    name = request.matchdict['short_name']
    publisher = Publisher.get(name)
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

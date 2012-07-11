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
    shared_template = get_renderer('templates/shared.pt').implementation()
    return dict(shared=shared_template,
                logged_in=authenticated_userid(request),
                )


@view_config(route_name='book_view', renderer='templates/book_view.pt')
def book_view(request):
    shared_template = get_renderer('templates/shared.pt').implementation()
    isbn13 = request.matchdict['isbn13']
    book = DBSession.query(Book).filter_by(isbn13=isbn13).first()
    if book is None:
        return HTTPNotFound('No such book')
    edit_url = request.route_url('book_edit', isbn13=isbn13)
    return dict(shared=shared_template,
                book=book,
                edit_url=edit_url,
                logged_in=authenticated_userid(request),
                )


@view_config(route_name='book_add', renderer='templates/book_edit.pt', permission='edit')
def book_add(request):
    shared_template = get_renderer('templates/shared.pt').implementation()
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
    return dict(shared=shared_template,
                book=book,
                save_url=save_url,
                logged_in=authenticated_userid(request),
                bindings=bindings,
                locations=locations,
                publishers=publishers,
                )


@view_config(route_name='book_edit', renderer='templates/book_edit.pt', permission='edit')
def book_edit(request):
    shared_template = get_renderer('templates/shared.pt').implementation()
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
    return dict(shared=shared_template,
                book=book,
                save_url=request.route_url('book_edit', isbn13=isbn13),
                logged_in=authenticated_userid(request),
                bindings=bindings,
                locations=locations,
                publishers=publishers,
                )


@view_config(route_name='book_delete', renderer='templates/book_delete.pt', permission='edit')
def book_delete(request):
    shared_template = get_renderer('templates/shared.pt').implementation()
    isbn13 = request.matchdict['isbn13']
    book = DBSession.query(Book).filter_by(isbn13=isbn13).one()
    if 'form.submitted' in request.params:
        DBSession.delete(book)
        return HTTPFound(location=request.route_url('book_list'))
    return dict(shared=shared_template,
                book=book,
                delete_url=request.route_url('book_delete', isbn13=isbn13),
                logged_in=authenticated_userid(request),
                )


@view_config(route_name='book_list', renderer='templates/book_list.pt')
def book_list(request):
    shared_template = get_renderer('templates/shared.pt').implementation()
    books = DBSession.query(Book).all()
    return dict(shared=shared_template,
                books=books,
                logged_in=authenticated_userid(request),
                book_url=lambda isbn13: request.route_url('book_view', isbn13=isbn13)
                )


@view_config(route_name='order_list', renderer='templates/order_list.pt')
def order_list(request):
    shared_template = get_renderer('templates/shared.pt').implementation()
    orders = DBSession.query(Order).all()
    return dict(shared=shared_template,
                orders=orders,
                logged_in=authenticated_userid,
                order_url=lambda po: request.route_url('order_view', po=po)
                )


@view_config(route_name='order_view', renderer='templates/order_view.pt')
def order_view(request):
    shared_template = get_renderer('templates/shared.pt').implementation()
    po = request.matchdict['po']
    order = DBSession.query(Order).filter_by(po=po).one()
    return dict(shared=shared_template,
                order=order,
                edit_url=request.route_url('order_edit', po=po),
                pdf_url=request.route_url('order_pdf', po=po),
                logged_in=authenticated_userid(request),
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
    shared_template = get_renderer('templates/shared.pt').implementation()
    save_url = request.route_url('order_add')
    shipping_methods = DBSession.query(ShippingMethod).all()
    distributors = DBSession.query(Distributor).all()
    return dict(shared=shared_template,
                save_url=save_url,
                logged_in=authenticated_userid(request),
                shipping_methods=shipping_methods,
                distributors=distributors,
                )


@view_config(route_name='order_edit', renderer='templates/edit_order.pt', permission='edit')
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
    shared_template = get_renderer('templates/shared.pt').implementation()
    shipping_methods = DBSession.query(ShippingMethod).all()
    distributors = DBSession.query(Distributor).all()
    return dict(shared=shared_template,
                order=order,
                message=message,
                save_url=request.route_url('order_edit', po=po),
                logged_in=authenticated_userid(request),
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
    shared_template = get_renderer('templates/shared.pt').implementation()
    return dict(shared=shared_template,
                order=order,
                delete_url=request.route_url('order_delete', po=po),
                logged_in=authenticated_userid(request),
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
    shared_template = get_renderer('templates/shared.pt').implementation()
    return dict(shared=shared_template,
                message=message,
                url=request.application_url + '/login',
                came_from=came_from,
                login=login,
                password=password,
                logged_in=False,
                )


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.route_url('front_page'), headers=headers)

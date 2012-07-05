from dateutil.parser import parse as parse_date

from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    )
from pyramid.view import (
    view_config,
    forbidden_view_config,
    )

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
    return dict(logged_in=authenticated_userid(request),
                )


@view_config(route_name='view_book', renderer='templates/single_book.pt')
def view_book(request):
    isbn13 = request.matchdict['isbn13']
    book = DBSession.query(Book).filter_by(isbn13=isbn13).first()
    if book is None:
        return HTTPNotFound('No such book')
    edit_url = request.route_url('edit_book', isbn13=isbn13)
    return dict(book=book,
                edit_url=edit_url,
                logged_in=authenticated_userid(request),
                editable=False,
                )


@view_config(route_name='add_book', renderer='templates/single_book.pt', permission='edit')
def add_book(request):
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
        authors = Author.parse_author_string(author_string)
        # TODO: validate data
        new_book = Book(isbn13, title, publisher, binding, shelf_location, authors=authors)
        DBSession.add(new_book)
        return HTTPFound(location=request.route_url('view_book', isbn13=isbn13))
    save_url = request.route_url('add_book')
    book = Book('', '', '', '', '', [])
    bindings = DBSession.query(Binding).all()
    locations = DBSession.query(ShelfLocation).all()
    publishers = DBSession.query(Publisher).all()
    return dict(book=book,
                save_url=save_url,
                logged_in=authenticated_userid(request),
                editable=True,
                bindings=bindings,
                locations=locations,
                publishers=publishers,
                )


@view_config(route_name='edit_book', renderer='templates/single_book.pt', permission='edit')
def edit_book(request):
    isbn13 = request.matchdict['isbn13']
    book = DBSession.query(Book).filter_by(isbn13=isbn13).one()
    if 'form.submitted' in request.params:
        # TODO: Validate data before accepting it.
        book.isbn13 = request.params['isbn13']
        book.title = request.params['title']
        book.authors = Author.parse_author_string(request.params['author_string'])
        book.publisher = DBSession.query(Publisher).filter_by(
                            short_name=request.params['publisher']).one()
        book.binding = DBSession.query(Binding).filter_by(
                            binding=request.params['binding']).one()
        book.shelf_location = DBSession.query(ShelfLocation).filter_by(
                            location=request.params['shelf_location']).one()
        DBSession.add(book)
        return HTTPFound(location=request.route_url('view_book', isbn13=book.isbn13))
    bindings = DBSession.query(Binding).all()
    locations = DBSession.query(ShelfLocation).all()
    publishers = DBSession.query(Publisher).all()
    return dict(book=book,
                save_url=request.route_url('edit_book', isbn13=isbn13),
                logged_in=authenticated_userid(request),
                editable=True,
                bindings=bindings,
                locations=locations,
                publishers=publishers,
                )


@view_config(route_name='delete_book', renderer='templates/delete_book.pt', permission='edit')
def delete_book(request):
    isbn13 = request.matchdict['isbn13']
    book = DBSession.query(Book).filter_by(isbn13=isbn13).one()
    if 'form.submitted' in request.params:
        DBSession.delete(book)
        return HTTPFound(location=request.route_url('list_books'))
    return dict(book=book,
                delete_url=request.route_url('delete_book', isbn13=isbn13),
                logged_in=authenticated_userid(request),
                )


@view_config(route_name='list_books', renderer='templates/book_list.pt')
def list_books(request):
    books = DBSession.query(Book).all()
    return dict(books=books,
                logged_in=authenticated_userid(request),
                )


@view_config(route_name="list_orders", renderer='templates/order_list.pt')
def list_orders(request):
    orders = DBSession.query(Order).all()
    return dict(orders=orders,
                logged_in=authenticated_userid,
                )


@view_config(route_name="view_order", renderer='templates/view_order.pt')
def view_order(request):
    po = request.matchdict['po']
    order = DBSession.query(Order).filter_by(po=po).one()
    return dict(order=order,
                edit_url=request.route_url('edit_order', po=po),
                pdf_url=request.route_url('make_order_pdf', po=po),
                logged_in=authenticated_userid(request),
                )


@view_config(route_name='make_order_pdf')
def make_order_pdf(request):
    po = request.matchdict['po']
    order = DBSession.query(Order).filter_by(po=po).one()
    filename = '/Users/bmbr/Orders/{}.pdf'.format(po)
    generate_order_pdf(order, filename)
    return HTTPFound(location=request.route_url('view_order', po=po))


@view_config(route_name="add_order", renderer='templates/add_order.pt', permission='edit')
def add_order(request):
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
        return HTTPFound(request.route_url('edit_order', po=po))
    save_url = request.route_url('add_order')
    shipping_methods = DBSession.query(ShippingMethod).all()
    distributors = DBSession.query(Distributor).all()
    return dict(save_url=save_url,
                logged_in=authenticated_userid(request),
                shipping_methods=shipping_methods,
                distributors=distributors,
                )


@view_config(route_name="edit_order", renderer='templates/edit_order.pt', permission='edit')
def edit_order(request):
    po = request.matchdict['po']
    order = DBSession.query(Order).filter_by(po=po).one()
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
        return HTTPFound(location=request.route_url('list_orders'))
    if 'new_entry.submitted' in request.params:
        book = DBSession.query(Book).filter_by(isbn13=request.params['isbn13']).one()
        quantity = request.params['quantity']
        ## TODO: validate the new entry
        entry = OrderEntry(order, book, quantity)
        DBSession.add(entry)
        return HTTPFound(location=request.route_url('edit_order', po=po))
    shipping_methods = DBSession.query(ShippingMethod).all()
    distributors = DBSession.query(Distributor).all()
    return dict(order=order,
                save_url=request.route_url('edit_order', po=po),
                logged_in=authenticated_userid(request),
                shipping_methods=shipping_methods,
                distributors=distributors,
                delete_entry_pattern=request.application_url + "/order/{po}/delete_entry/{isbn13}",
                )


@view_config(route_name='delete_order', renderer='templates/delete_order.pt', permission='edit')
def delete_order(request):
    po = request.matchdict['po']
    order = DBSession.query(Order).filter_by(po=po).one()
    if 'form.submitted' in request.params:
        DBSession.delete(order)
        return HTTPFound(location=request.route_url('list_orders'))
    return dict(order=order,
                delete_url=request.route_url('delete_order', po=po),
                logged_in=authenticated_userid(request),
                )


@view_config(route_name='delete_order_entry', permission='edit')
def delete_order_entry(request):
    po = request.matchdict['po']
    isbn13 = request.matchdict['isbn13']
    order = DBSession.query(Order).filter_by(po=po).one()
    book = DBSession.query(Book).filter_by(isbn13=isbn13).one()
    order_entry = DBSession.query(OrderEntry).filter_by(order=order, book=book).one()
    DBSession.delete(order_entry)
    return HTTPFound(location=request.route_url('edit_order', po=po))


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

    return dict(message=message,
                url=request.application_url + '/login',
                came_from=came_from,
                login=login,
                password=password,
                )


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.route_url('front_page'), headers=headers)

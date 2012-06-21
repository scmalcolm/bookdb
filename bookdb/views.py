import datetime

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
    )

from .security import USERS


@view_config(route_name='front_page', renderer='templates/front_page.pt')
def front_page(request):
    pass


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
        author_name = request.params['author_name']
        publisher = DBSession.query(Publisher).filter_by(
                            short_name=request.params['publisher']).one()
        binding = DBSession.query(Binding).filter_by(
                            binding=request.params['binding']).one()
        shelf_location = DBSession.query(ShelfLocation).filter_by(
                            location=request.params['shelf_location']).one()
        # TODO: validate data
        new_book = Book(isbn13, title, author_name, publisher, binding, shelf_location)
        DBSession.add(new_book)
        return HTTPFound(location=request.route_url('view_book', isbn13=isbn13))
    save_url = request.route_url('add_book')
    book = Book('', '', '', '', '', '')
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
        book.author_name = request.params['author_name']
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


@view_config(route_name="edit_order", renderer='templates/edit_order.pt', permission='edit')
def edit_order(request):
    po = request.matchdict['po']
    order = DBSession.query(Order).filter_by(po=po).one()
    if 'header.submitted' in request.params:
        po = request.params['po']
        order_date = request.params['order_date']
        # TODO: validate new header data
        return HTTPNotFound(order_date)
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

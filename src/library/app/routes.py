from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from .base import db
from .models import Library, Book, LibraryBook
from . import schemas

api = Blueprint('api', __name__)

BOOKS_COUNT_TEMPLATE = (
    db.select(db.func.count(Book.id))
    .join_from(Book, LibraryBook, Book.id == LibraryBook.book_id)
    .join(Library)
)
BOOKS_ITEMS_TEMPLATE = (
    db.select(*Book.__table__.columns, LibraryBook.available_count)
    .join(LibraryBook)
    .join(Library)
)


def format_errors(messages):
    for field, errors in messages.items():
        for error in errors:
            yield {'field': field, 'error': error}


def format_validation_error(text, error):
    return {
        'message': text,
        'errors': list(format_errors(error.messages))
    }


@api.route('/libraries', methods=['GET'])
def list_libraries():
    try:
        args = schemas.LibraryPaginationRequestSchema().load(request.args)
    except ValidationError as err:
        return jsonify(format_validation_error('Invalid data', err)), 400

    libraries = db.paginate(
        db.select(Library).where(Library.city == args['city']),
        page=args.get('page'),
        per_page=args.get('size'),
        count=True
    )

    return jsonify(schemas.LibraryPaginationResponseSchema().dump(libraries)), 200


@api.route('/libraries/<library_uid>', methods=['GET'])
def get_library(library_uid):
    library = db.session.execute(
        db.select(Library).where(Library.library_uid == library_uid)
    ).scalars().first()
    if library is None:
        return jsonify({}), 404
    return jsonify(schemas.LibrarySchema().dump(library)), 200


@api.route('/libraries/<library_uid>/books', methods=['GET'])
def get_library_books(library_uid):
    try:
        args = schemas.LibraryBookPaginationRequestSchema().load(request.args)
    except ValidationError as err:
        return jsonify(format_validation_error('Invalid data', err)), 400

    page = args.get('page', 1)
    per_page = args.get('size', 20)
    show_all = args.get('show_all', False)

    books_count_stmt = BOOKS_COUNT_TEMPLATE.where(Library.library_uid == library_uid)
    books_items_stmt = BOOKS_ITEMS_TEMPLATE.where(Library.library_uid == library_uid)

    if not show_all:
        books_count_stmt = books_count_stmt.where(LibraryBook.available_count > 0)
        books_items_stmt = books_items_stmt.where(LibraryBook.available_count > 0)

    books_count = db.session.execute(books_count_stmt).scalars().one()
    books_items = db.session.execute(
        books_items_stmt.limit(per_page).offset((page - 1) * per_page)
    ).all()

    return jsonify(schemas.LibraryBookPaginationResponseSchema().dump({
        "items": books_items,
        "page": page,
        "per_page": per_page,
        "total": books_count
    })), 200


@api.route('/books/<book_uid>', methods=['GET'])
def get_book(book_uid):
    book = db.session.execute(
        db.select(Book).where(Book.book_uid == book_uid)
    ).scalars().first()
    if book is None:
        return jsonify({}), 404
    return jsonify(schemas.BookSchema().dump(book)), 200


@api.route('/libraries/<library_uid>/books/<book_uid>', methods=['PATCH'])
def edit_library_book(library_uid, book_uid):
    library_book = db.session.execute(
        db.select(LibraryBook).join(Library).join(Book)
        .where(Library.library_uid == library_uid, Book.book_uid == book_uid)
    ).scalars().first()
    if library_book is None:
        return jsonify({'message': 'not found'}), 404

    args = schemas.LibraryBookResponseSchema().load(request.json)
    if 'available_count' in args.keys():
        library_book.available_count = args['available_count']
    if 'condition' in args.keys():
        library_book.book.condition = args['condition']
    db.session.commit()

    data = schemas.LibraryBookResponseSchema().dump(library_book.book)
    data['available_count'] = library_book.available_count
    return jsonify(data), 200

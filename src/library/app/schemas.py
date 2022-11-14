from marshmallow import Schema, fields, validate
from marshmallow_enum import EnumField

from .models import Book


class LibraryPaginationRequestSchema(Schema):
    city = fields.String(required=True)
    page = fields.Integer(validate=validate.Range(min=0))
    size = fields.Integer(validate=validate.Range(min=1, max=100))


class LibrarySchema(Schema):
    library_uid = fields.UUID(data_key='libraryUid')
    name = fields.String()
    address = fields.String()
    city = fields.String()


class LibraryPaginationResponseSchema(Schema):
    page = fields.Integer()
    per_page = fields.Integer(data_key='pageSize')
    total = fields.Integer(data_key='totalElements')
    items = fields.List(fields.Nested(LibrarySchema))


class LibraryBookPaginationRequestSchema(Schema):
    page = fields.Integer(validate=validate.Range(min=0))
    size = fields.Integer(validate=validate.Range(min=1, max=100))
    show_all = fields.Boolean(data_key='showAll')


class BookSchema(Schema):
    book_uid = fields.UUID(data_key='bookUid')
    name = fields.String()
    author = fields.String()
    genre = fields.String()
    condition = EnumField(Book.Condition)


class LibraryBookResponseSchema(BookSchema):
    available_count = fields.Integer(data_key='availableCount')


class LibraryBookPaginationResponseSchema(Schema):
    page = fields.Integer()
    per_page = fields.Integer(data_key='pageSize')
    total = fields.Integer(data_key='totalElements')
    items = fields.List(fields.Nested(LibraryBookResponseSchema))

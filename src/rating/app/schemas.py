from marshmallow import Schema, fields


class RatingSchema(Schema):
    username = fields.String(load_only=True, required=True)
    stars = fields.Integer()

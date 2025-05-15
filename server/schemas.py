from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    password = fields.Str(required=False, validate=validate.Length(min=6))

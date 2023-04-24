import bson
import bson.errors as errors
from pydantic import BaseModel as _BaseModel


class ObjectId(bson.ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        try:
            return cls(value)
        except errors.InvalidId:
            raise ValueError("Not a valid ObjectId")

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class BaseModel(_BaseModel):
    class Config:
        json_encoders = {ObjectId: str}

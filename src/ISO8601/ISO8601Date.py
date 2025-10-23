import re
from typing import Any, Dict, Optional, Pattern, Union, AnyStr, no_type_check

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

from pydantic_schemaorg.ISO8601 import errors

_url_regex_cache: Union[Pattern[AnyStr], None] = None


def ISO8601Date_regex() -> Pattern[str]:
    global _url_regex_cache
    if _url_regex_cache is None:
        _url_regex_cache = re.compile(
            r'(?P<year>-?(?:[1-9][0-9]*)?[0-9]{4})-?(?P<month>1[0-2]|0[1-9])?-?(?P<day>3[01]|0[1-9]|[12][0-9])?(T(?P<hour>(2[0-3]|[01][0-9])))?(\:(?P<minute>[0-5][0-9]))?(\:(?P<second>[0-5][0-9]))?(\.(?P<microsecond>[0-9]+))?([+-](?P<timezone>([0-9]{2}\:[0-9]{2})|Z))?',
            re.IGNORECASE,
        )
    return _url_regex_cache


class ISO8601Date(str):
    strip_whitespace = True
    min_length = 1
    max_length = 2 ** 16

    __slots__ = ('date', 'year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond', 'tz')

    @no_type_check
    def __new__(cls, date: Optional[str], **kwargs) -> object:
        return str.__new__(cls, cls.build(**kwargs) if date is None else date)

    def __init__(
        self,
        date: str,
        *,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        second: Optional[int] = None,
        microsecond: Optional[int] = None,
        tz: Optional[str] = None,
    ) -> None:
        str.__init__(date)
        self.date = date
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.microsecond = microsecond
        self.tz = tz

    @classmethod
    def build(
        cls,
        date: str,
        *,
        year: int,
        month: Optional[int] = None,
        day: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        second: Optional[int] = None,
        microsecond: Optional[int] = None,
        tz: Optional[str] = None,
    ) -> str:
        date = ''
        if year:
            date += str(year)
            if month:
                date += '-' + str(month)
                if day:
                    date += '-' + str(month)
                    if hour:
                        date += 'T' + str(hour)
                        if minute:
                            date += ':' + str(minute)
                            if second:
                                date += ':' + str(second)
                                if microsecond:
                                    date += '.' + str(microsecond)
        return date

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        str_schema = core_schema.str_schema(
            min_length=cls.min_length,
            max_length=cls.max_length,
            strip_whitespace=cls.strip_whitespace,
        )
        return core_schema.no_info_after_validator_function(cls.validate, str_schema)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(schema)
        if isinstance(json_schema, dict):
            json_schema.setdefault('format', 'ISO8601')
            json_schema.setdefault('minLength', cls.min_length)
            json_schema.setdefault('maxLength', cls.max_length)
        return json_schema

    @classmethod
    def validate(cls, value: Any) -> 'ISO8601Date':
        if isinstance(value, cls):
            return value
        value = str(value)
        if cls.strip_whitespace:
            value = value.strip()

        match = ISO8601Date_regex().match(value)
        if not match or match.end() != len(value):
            raise errors.ISO8601DateInvalid()

        parts = match.groupdict()
        parts = cls.validate_parts(parts)

        return cls(
            value,
            year=parts['year'],
            month=parts['month'],
            day=parts['day'],
            hour=parts['hour'],
            minute=parts['minute'],
            second=parts['second'],
            microsecond=parts['microsecond'],
            tz=parts['tz'],
        )

    @classmethod
    def validate_parts(cls, parts: Dict[str, str]) -> Dict[str, Union[str, int]]:
        parts_order = ['year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond', 'tz']
        year = parts['year']
        if year is None:
            raise errors.ISO8601DateInvalid()

        for part_order in parts_order:
            parts[part_order] = parts.get(part_order, None)
            if parts[part_order] is not None and part_order != 'tz':
                parts[part_order] = int(parts[part_order])

        return parts

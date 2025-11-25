from rest_framework.serializers import (
    Field,
)

from Extension.abc.MyString import str_to_list
from Extension.abc.MyList import clear_list_empty



class TagListField(Field):
    def to_internal_value(self, data:'str|list[str]') -> 'list[str]':
        if isinstance(data, str):
            data = str_to_list(data)
        if not isinstance(data, list):
            self.fail('not_a_list', input_type=type(data).__name__)
        return clear_list_empty(data)

    def to_representation(self, value:'list[str]') -> 'list[str]':
        if isinstance(value, str):
            value = [value]
        return value


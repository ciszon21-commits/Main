from collections.abc import Generator
from typing import (
    Callable,
    TypeVar,
)




_T = TypeVar('_T')



def zip_list_by_count(ml, count):
    result = []
    mlLen = len(ml)
    loop = mlLen // count
    loop = loop if mlLen%count == 0 else loop+1
    for i in range(loop):
        start = i * count
        end = (i+1) * count
        item = ml[start: end]
        result.append(item)
    return result


def clear_list_empty(lst:'list[_T]') -> 'list[_T]':
    checkLam:'Callable[[_T],bool]' = lambda i: True if i else False
    return list(filter(checkLam, lst))




def chunk_list_yield(lst:'list[_T]', size:'int') -> 'Generator[_T]':
    for i in range(0, len(lst), size):
        yield lst[i: i+size]
def chunk_list(lst:'list[_T]', size:'int') -> 'list[list[_T]]':
    return list(chunk_list_yield(lst, size))



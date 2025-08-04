# statequark

Jotai-inspired atomic state management for Python.

## Installation

pip install statequark

## Usage

from statequark import quark

count = quark(0)
print(count.value) # 0

count.set_sync(1)
print(count.value) # 1

## Derived Quark Example

def double_getter(get):
return get(count) \* 2

double = quark(double_getter, deps=[count])
print(double.value) # 2

## License

MIT

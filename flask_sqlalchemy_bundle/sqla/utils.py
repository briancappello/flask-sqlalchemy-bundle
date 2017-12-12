import re
import unicodedata

# aliases
from flask_application_factory import (
    camel_to_snake_case,
    title_case,
)


def pluralize(name):
    if name.endswith('y'):
        # right replace 'y' with 'ies'
        return 'ies'.join(name.rsplit('y', 1))
    elif name.endswith('s'):
        return f'{name}es'
    return f'{name}s'


def slugify(string):
    string = re.sub(r'[^\w\s-]', '',
                    unicodedata.normalize('NFKD', string.strip()))
    return re.sub(r'[-\s]+', '-', string).lower()

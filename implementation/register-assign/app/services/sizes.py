"""Sizes, used by registration and assignment."""
from ..errors import InvalidParcelData
from ..models import SizeCategory

SIZE_RANK = {size: rank for rank, size in enumerate(SizeCategory)}


def parse_size(value: str) -> SizeCategory:
    """Returns the size for a string such as "small" or "MEDIUM". Raises InvalidParcelData for an unknown size."""
    try:
        return SizeCategory(value.strip().upper())
    except ValueError:
        raise InvalidParcelData("Size must be SMALL, MEDIUM or LARGE") from None

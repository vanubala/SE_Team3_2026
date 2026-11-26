"""Sizes, used by registration and assignment."""
from app.db.models import SizeCategory
from app.services.parcel_errors import InvalidParcelData

SIZE_RANK = {size: rank for rank, size in enumerate(SizeCategory)}


def parse_size(value: str) -> SizeCategory:
    """Returns the size for a string such as "small" or "MEDIUM". Raises InvalidParcelData for an unknown size."""
    try:
        return SizeCategory(value.strip().upper())
    except ValueError:
        raise InvalidParcelData("Size must be SMALL, MEDIUM or LARGE") from None

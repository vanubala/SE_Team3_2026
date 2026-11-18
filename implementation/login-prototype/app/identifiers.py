"""Recognises what a person typed into the shared sign-in field.

Rules:
- Couriers:        CO + 5 digits (company provided), e.g. CO00001
- Administrators:  AD + 5 digits (company provided), e.g. AD00001
- Senders and recipients: an email address or a phone number in
  international format, e.g. name@example.com or +352 621 123 456
"""
from dataclasses import dataclass
from enum import Enum
import re


class IdentifierKind(str, Enum):
    COURIER_ID = "COURIER_ID"
    ADMIN_ID = "ADMIN_ID"
    EMAIL = "EMAIL"
    PHONE = "PHONE"


@dataclass(frozen=True)
class Identifier:
    kind: IdentifierKind
    value: str  # normalised form used for lookups

    @property
    def is_staff(self) -> bool:
        return self.kind in (IdentifierKind.COURIER_ID, IdentifierKind.ADMIN_ID)

    @property
    def masked(self) -> str:
        """Version that is safe to show back on screen."""
        if self.kind is IdentifierKind.EMAIL:
            local, domain = self.value.split("@", 1)
            return f"{local[0]}***@{domain}"
        if self.kind is IdentifierKind.PHONE:
            return self.value[:4] + "*" * (len(self.value) - 6) + self.value[-2:]
        return self.value


class InvalidIdentifier(ValueError):
    pass


STAFF_ID = re.compile(r"(CO|AD)(\d{5})")
LOOKS_LIKE_STAFF_ID = re.compile(r"(CO|AD)\d", re.IGNORECASE)
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[a-z]{2,}")
PHONE = re.compile(r"\+[1-9]\d{7,14}")
PHONE_SEPARATORS = re.compile(r"[\s\-.()]")


def parse_identifier(raw: str) -> Identifier:
    text = (raw or "").strip()
    if not text:
        raise InvalidIdentifier("Enter your company ID, email address or phone number.")
    if len(text) > 254:
        raise InvalidIdentifier("This value is too long.")

    if "@" in text:
        email = text.lower()
        if not EMAIL.fullmatch(email):
            raise InvalidIdentifier("Enter a valid email address.")
        return Identifier(IdentifierKind.EMAIL, email)

    if LOOKS_LIKE_STAFF_ID.match(text):
        match = STAFF_ID.fullmatch(text.upper())
        if not match:
            raise InvalidIdentifier("Company IDs are CO or AD followed by 5 digits, for example CO00001.")
        kind = IdentifierKind.COURIER_ID if match.group(1) == "CO" else IdentifierKind.ADMIN_ID
        return Identifier(kind, text.upper())

    phone = PHONE_SEPARATORS.sub("", text)
    if phone.startswith("00"):
        phone = "+" + phone[2:]
    if PHONE.fullmatch(phone):
        return Identifier(IdentifierKind.PHONE, phone)
    if re.fullmatch(r"\+?\d+", phone):
        raise InvalidIdentifier(
            "Enter the phone number in international format, for example +352 621 123 456."
        )
    raise InvalidIdentifier(
        "Enter a company ID (CO or AD + 5 digits), an email address or a phone number."
    )

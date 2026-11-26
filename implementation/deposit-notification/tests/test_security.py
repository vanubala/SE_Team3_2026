import pytest

from deposit_notification.security import PickupCodeIssuer


def test_issued_code_is_six_digits_and_verifiable():
    issuer = PickupCodeIssuer("s" * 32)

    code = issuer.issue()

    assert len(code.plaintext) == 6
    assert code.plaintext.isascii() and code.plaintext.isdigit()
    assert issuer.verify(code.plaintext, code.code_hash)
    assert not issuer.verify("not-a-pin", code.code_hash)
    assert not issuer.verify("000000", "wrong-hash")


def test_hash_rejects_non_six_digit_codes():
    issuer = PickupCodeIssuer("s" * 32)

    with pytest.raises(ValueError, match="exactly six digits"):
        issuer.hash_code("12345")


def test_secret_must_be_at_least_32_bytes():
    with pytest.raises(ValueError, match="at least 32 bytes"):
        PickupCodeIssuer("short")

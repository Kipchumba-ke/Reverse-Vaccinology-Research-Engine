import pytest

from app.services import auth_service


class _NoUsers:
    def find_by_email(self, email):
        return None


def test_unknown_email_still_runs_a_password_check(monkeypatch):
    # Rejecting an unknown email without hashing would be measurably faster
    # than rejecting a wrong password, which reveals who has an account.
    checked = []
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, password_hash: checked.append(password_hash) or False,
    )

    with pytest.raises(ValueError, match="Invalid email or password"):
        auth_service.AuthService(_NoUsers()).login(
            "nobody@example.com", "whatever-password"
        )

    assert checked == [auth_service._UNKNOWN_USER_HASH]

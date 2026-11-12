"""Stand-in for the Notification Gateway (SMS / email provider).

No real provider is connected, so messages are printed in the terminal that
runs the server. Replace ConsoleGateway with a real client later; the rest of
the code only calls send_code().
"""
from .identifiers import Identifier, IdentifierKind


class ConsoleGateway:
    def send_code(self, identifier: Identifier, code: str, purpose: str) -> None:
        channel = "SMS" if identifier.kind is IdentifierKind.PHONE else "EMAIL"
        action = "finish creating your account" if purpose == "REGISTER" else "sign in"
        print(f"[outbox] {channel} to {identifier.value}: "
              f"Your Smart Parcel Locker code is {code}. Use it to {action}.", flush=True)

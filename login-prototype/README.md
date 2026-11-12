# Smart Parcel Locker - Shared Sign-in Prototype

A standalone prototype of **one sign-in page for every type of user**. It is completely separate from `implementation/parcel-registration` and shares no code with it.

| Who | Signs in with | Can register here? |
|---|---|---|
| Courier | Company ID `CO` + 5 digits (e.g. `CO00001`) and a password | No - provided by the company |
| Administrator | Company ID `AD` + 5 digits (e.g. `AD00001`) and a password | No - hardcoded from the start |
| Sender / recipient | Email address or phone number, then a 6-digit one-time code | Yes |

After signing in, everyone lands on `/dashboard`, which shows content for their role and an access check proving the server only answers each role's own area.

## Start it

You need **Python 3.10 or newer**. Check with `python --version` (on Windows you can also use `py --version`).

Open a terminal in this folder (`login-prototype`) and run:

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

If PowerShell refuses to run `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

Then open **http://127.0.0.1:8000** in your browser. Stop the server with `Ctrl+C`.

Next time you only need to activate the environment (second line) and run `python run.py`.

### What the terminal shows

```text
Smart Parcel Locker - shared sign-in prototype
Open http://127.0.0.1:8000 in your browser. Press Ctrl+C to stop.

Company accounts (new passwords on every start):
  ID        Role           Name             Password
  AD00001   Administrator  Morgan Weber     q3Xv-7yLmP2a
  AD00002   Administrator  Lea Schmit       ...
  CO00001   Courier        Tom Muller       ...
  CO00002   Courier        Sara Hoffmann    ...
  CO00003   Courier        Jonas Klein      ...
```

Use these IDs and passwords to sign in as staff. One-time codes for senders and recipients are printed below this table as `[outbox]` lines, and also shown on the page, because no SMS or email provider is connected.

### Options

| Command | Effect |
|---|---|
| `python run.py --staff-password "Demo-Pass-2026"` | Same password for every staff account (handy for a presentation). At least 8 characters. |
| `python run.py --port 8080` | Use another port if 8000 is taken. |
| `python run.py --reset` | Delete the local database first (removes registered senders/recipients). |

## Try it

1. **Courier:** type `CO00001`. The page recognises a courier ID and asks for the password from the terminal.
2. **Administrator:** type `AD00001` and its password. The dashboard lists every account in the system.
3. **Register a sender / recipient:** click *Create an account*, enter a name and an email (`ana@example.com`) or phone (`+352 621 123 456`), then enter the code shown on screen.
4. **Sign in as that sender / recipient:** go back to sign-in, type the same email or phone, and enter the new code.
5. **Rules being enforced:**
   - Try registering with `CO00009` or `AD00001`: refused.
   - Enter a wrong password 5 times: the account locks for 15 minutes.
   - Use a code twice or after 10 minutes: refused.

## Run the tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

49 tests cover every rule above: ID formats, lockout, code expiry and single use, registration limits, role-based access and the pages.

## How it maps to the team's requirements

| Requirement in the repo | How the prototype handles it |
|---|---|
| Shared *Authenticate* use case (global use case diagram) | One page at `/` for all roles |
| FR_05 role-based access: recipient, sender, courier, administrator | Roles `COURIER`, `ADMINISTRATOR`, `CUSTOMER` (sender and recipient in one account); every API area checks the role |
| C0 courier signs in with delivery-company account | `CO` + 5 digits and a password, tied to a company |
| Admin authentication: existing company account | `AD` + 5 digits, hardcoded in `app/seed.py`, no way to create more |
| R0 / recipient use case: email or phone, temporary verification code | 6-digit one-time code, valid 10 minutes, single use |
| FR_01 users register with email or phone | Registration accepts only email or phone; company IDs are rejected by the API and by a database constraint |
| NFR_01 login endpoints must be secure | Hashed passwords (scrypt), hashed codes, signed tokens, lockout, no hints about which accounts exist, strict security headers |
| NFR_06 (5 attempts, 15-minute block) | Same rule applied to staff passwords and customer codes |

## API

| Method and path | Purpose |
|---|---|
| `POST /api/auth/login` | Staff sign-in: `{identifier, password}` |
| `POST /api/auth/code` | Send a sign-in code to an email/phone: `{identifier}` |
| `POST /api/auth/code/verify` | Sign in with the code: `{identifier, code}` |
| `POST /api/auth/register` | Start sender/recipient registration: `{name, identifier}` |
| `POST /api/auth/register/verify` | Finish registration with the code: `{identifier, code}` |
| `GET /api/me` | Current account |
| `GET /api/courier/overview` | Courier only |
| `GET /api/admin/accounts` | Administrator only |
| `GET /api/customer/overview` | Sender/recipient only |

Successful sign-in returns a JWT (HS256) with `sub`, `role`, `name`, `iss=smart-locker-auth`, `aud=smart-locker-api` and `exp` (60 minutes). These are the same claim names the parcel-registration prototype checks, which keeps a later merge simple. Interactive API docs are at http://127.0.0.1:8000/docs.

## Files

```text
run.py                start script (localhost only)
app/identifiers.py    recognises CO / AD / email / phone
app/services.py       sign-in and registration rules (no HTTP code)
app/api.py            endpoints and role checks
app/repository.py     SQLite tables and constraints
app/seed.py           hardcoded administrator and courier accounts
app/security.py       password hashing, codes, tokens
app/notifications.py  stand-in for the SMS/email gateway
static/               sign-in, registration and dashboard pages
tests/                automated tests
```

## Prototype limitations

These are deliberate simplifications for the team to decide on before real use:

- **Codes appear on screen and in the terminal** because there is no SMS/email gateway. Set `show_codes_on_screen=False` and replace `ConsoleGateway` once one exists.
- **Staff passwords change on every start** unless `--staff-password` is used. Only hashes are stored; no password is written in the code.
- **No password reset, account deletion (FR_08) or "admin creates a courier" screen yet.**
- **Couriers are seeded like admins** for now; the requirements say administrators will manage courier accounts later.
- **Some answers still reveal that an account exists.** "Wait 30 seconds" and "account locked" only appear for real accounts.
- **The session token is kept in the browser tab** (`sessionStorage`) and expires after 60 minutes. Closing the tab signs you out.
- **The server only listens on 127.0.0.1**, so it cannot be reached from other computers.

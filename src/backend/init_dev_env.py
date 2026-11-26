"""Create local development credentials without overwriting an existing .env."""
import os
from pathlib import Path
from secrets import token_urlsafe
from uuid import uuid4


def main():
    target = Path(__file__).resolve().parent / '.env'
    db_password, jwt_secret, courier_password, admin_password = (token_urlsafe(32) for _ in range(4))
    body = '\n'.join([
        'POSTGRES_DB=smart_locker', 'POSTGRES_USER=locker_dev',
        f'POSTGRES_PASSWORD={db_password}',
        f'DATABASE_URL=postgresql+psycopg://locker_dev:{db_password}@127.0.0.1:5432/smart_locker',
        f'JWT_SECRET={jwt_secret}', 'JWT_ISSUER=smart-locker-auth',
        'JWT_AUDIENCE=smart-locker-api', 'JWT_TTL_MINUTES=30',
        'CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]',
        f'PARCEL_ID_NAMESPACE={uuid4()}',
        f'DEMO_COURIER_PASSWORD={courier_password}', f'DEMO_ADMIN_PASSWORD={admin_password}', ''
    ])
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print('.env already exists; no credentials changed.')
        return
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(body)
    print('Created local .env. Read it locally for demo passwords. Never commit or share this file.')


if __name__ == '__main__':
    main()

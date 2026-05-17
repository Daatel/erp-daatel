import psycopg2
from psycopg2.extensions import parse_dsn

dsn1 = "postgresql://user:pass@host:6543/db?pgbouncer=true"
dsn2 = "postgresql://user:pass@host:6543/db"

try:
    print(parse_dsn(dsn1))
except Exception as e:
    print("DSN1 error:", repr(e))

try:
    print(parse_dsn(dsn2))
except Exception as e:
    print("DSN2 error:", repr(e))

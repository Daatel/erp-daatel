import database

pool = database.init_connection_pool()
print("Connection Pool:", pool)
if pool is not None:
    print("Using PostgreSQL!")
else:
    print("Using SQLite erp_fabrica.db!")

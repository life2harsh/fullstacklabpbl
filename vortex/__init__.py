try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    # SQLite-only local environments do not need the MySQL driver.
    pass

from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
import psycopg2.extras

db_config = {
    "host": "localhost",
    "database": "credi_facil",
    "user": "uacm",
    "password": "uacm1",
    "port": 5432  # Agregar puerto explícito
}

class PostgresDB:
    def __init__(self):
        self.app = None
        self.pool = None

    def init_app(self, app):
        self.app = app
        self.connect()

    def connect(self):
        self.pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=30,
            **db_config
        )

    @contextmanager
    def get_cursor(self, commit=False):
        if self.pool is None:
            self.connect()
        con = self.pool.getconn()
        try:
            yield con.cursor(cursor_factory=psycopg2.extras.DictCursor)
            if commit:
                con.commit()
        except Exception as e:
            con.rollback()
            raise e
        finally:
            self.pool.putconn(con)

    # Método para verificar credenciales
    def verificar_usuario(self, usuario, contrasena):
        with self.get_cursor() as cur:
            cur.execute(
                """SELECT id, usuario 
                FROM usuarios 
                WHERE usuario = %s 
                AND contrasena_hash = crypt(%s, contrasena_hash)""",
                (usuario, contrasena)
            )
            return cur.fetchone()
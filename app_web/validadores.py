from postgres_db import PostgresDB  

class RegistroError(Exception):
    pass

class UsuarioValidator:
    def __init__(self, db: PostgresDB):
        self.db = db
    
    def usuario_existe(self, usuario: str) -> bool:
        """
        Verifica si un nombre de usuario ya existe en la base de datos
        """
        try:
            with self.db.get_cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM usuarios WHERE usuario = %s",
                    (usuario,)
                )
                return cur.fetchone() is not None
                
        except Exception as e:
            # Loggear el error si es necesario
            raise RegistroError("Error al verificar usuario") from e


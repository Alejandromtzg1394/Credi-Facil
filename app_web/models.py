from flask import session
from flask import current_app
import re
from typing import Dict, Any
from datetime import date, timedelta
from .extension import pgdb
from decimal import Decimal, ROUND_HALF_UP

class DBException(Exception):
    pass

class PagoError(Exception):
    pass

class UsuarioError(Exception):
    pass

class Usuario:

    def __init__(self, 
                 id=None,
                 nombre= None,
                 apellido_paterno= None,
                 apellido_materno= None,
                 edad= None,
                 ingreso_mensual= None,
                 usuario= None,
                 contrasena = None,
                 validar = True):
        
        if validar:
            # Validaciones existentes
            if not nombre or len(nombre) >= 25 or not re.fullmatch(r"[A-Za-zÁÉÍÓÚÑáéíóúñ ]+", nombre):
                raise UsuarioError("Nombre inválido o vacío")
            
            for apellido, tipo in [(apellido_paterno, "paterno"), (apellido_materno, "materno")]:
                if not apellido or len(apellido) >= 25 or not re.fullmatch(r"[A-Za-zÁÉÍÓÚÑáéíóúñ ]+", apellido):
                    raise UsuarioError(f"Apellido {tipo} inválido o vacío")

            if not isinstance(edad, int) or not (18 <= edad <= 65):
                raise UsuarioError("Edad debe ser entero entre 18-65")

            if ingreso_mensual is None or ingreso_mensual <= 0:
                raise UsuarioError("Ingreso mensual inválido")
            
            if not usuario or len(usuario) >= 15 or not re.fullmatch(r"^[a-zA-Z0-9_]+$", usuario):
                raise UsuarioError("Usuario debe contener solo caracteres alfanuméricos y _ (máx 15)")

            if (not contrasena or len(contrasena) != 4 
                or not re.fullmatch(r"^\d{4}$", contrasena)):
                raise UsuarioError("La contraseña debe ser 4 dígitos numéricos")
            

        # Atributos base
        self.id = id
        self.nombre = nombre
        self.apellido_paterno = apellido_paterno
        self.apellido_materno = apellido_materno
        self.edad = edad
        self.ingreso_mensual =  ingreso_mensual
        self.usuario = usuario
        self.contrasena = contrasena


    @classmethod
    def consultar_usuario(cls, usuario_nombre):
        """Consulta un usuario por su nombre de usuario y su crédito"""
        with pgdb.get_cursor() as cur:
            # Obtener datos del usuario
            cur.execute("""
                SELECT id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena
                FROM usuarios
                WHERE usuario = %s
            """, (usuario_nombre,))
            row = cur.fetchone()
            if not row:
                return None

            usuario = cls(
                id=row[0],
                nombre=row[1],
                apellido_paterno=row[2],
                apellido_materno=row[3],
                edad=row[4],
                ingreso_mensual=row[5],
                usuario=row[6],
                contrasena=row[7],
                validar=True
            )

            # Obtener crédito del usuario
            cur.execute("""
                SELECT monto_credito, tasa_interes, plazo_meses, pago_mensual, total_con_interes
                FROM creditos
                WHERE id_usuario = %s
            """, (usuario.id,))
            credito_row = cur.fetchone()
            if credito_row:
                usuario.credito = {
                    'monto_credito': credito_row[0],
                    'tasa_interes': credito_row[1],
                    'plazo_meses': credito_row[2],
                    'pago_mensual': credito_row[3],
                    'total_credito_con_interes': credito_row[4],
                }
            else:
                usuario.credito = None

            return usuario
        
    @staticmethod
    def consultar_pagos(id_usuario):
        """Consulta todos los pagos del usuario"""
        with pgdb.get_cursor() as cur:
            cur.execute("""
                SELECT id_pago, fecha_pago, monto, estado_pago
                FROM pagos
                WHERE id_usuario = %s
                ORDER BY fecha_pago
            """, (id_usuario,))
            pagos = cur.fetchall()
            return [{
                'id_pago': r[0],
                'fecha_pago': r[1],
                'monto': r[2],
                'estado_pago': r[3]
            } for r in pagos]



    @classmethod
    def verificar_credenciales(cls, usuario, contrasena):
        try:
            with pgdb.get_cursor() as cur:
                cur.execute("""
                    SELECT id, usuario, contrasena FROM usuarios
                    WHERE usuario = %s AND contrasena = %s
                """, (usuario, contrasena))
                resultado = cur.fetchone()

                if resultado:
                    return {'id': resultado[0], 'usuario': resultado[1]}
                else:
                    return None

        except Exception as e:
            print(f"[Error] verificar_credenciales: {e}")
            raise UsuarioError("Error técnico al verificar credenciales")  # Aquí se lanza


    def guardar(self):
        try:
            with self.db.get_cursor(commit=True) as cur:

                # Verificar si el usuario ya existe
                cur.execute(
                    "SELECT id FROM usuarios WHERE usuario = %s",
                    (self.usuario,)
                )
                if cur.fetchone():
                    raise UsuarioError("El usuario ya existe")

                # Insertar usuario y obtener su ID
                cur.execute(
                    """INSERT INTO usuarios 
                    (nombre, apellido_paterno, apellido_materno, edad, 
                    ingreso_mensual, usuario, contrasena) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id""",
                    (self.nombre, self.apellido_paterno, self.apellido_materno,
                    self.edad, self.ingreso_mensual, self.usuario, self.contrasena)
                )

                resultado = cur.fetchone()
                if not resultado:
                    raise UsuarioError("Error al crear el usuario")

                self.id = resultado[0]

                # Calcular crédito
                datos_credito = Usuario.calcular_credito(ingreso_mensual=self.ingreso_mensual)

                # Insertar crédito
                cur.execute("""
                    INSERT INTO creditos (
                        id_usuario, monto_credito, tasa_interes, plazo_meses,
                        pago_mensual, total_con_interes
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    self.id,
                    datos_credito['monto_credito'],
                    datos_credito['tasa_interes'],
                    datos_credito['plazo_meses'],
                    datos_credito['pago_mensual'],
                    datos_credito['total_credito_con_interes']
                ))

                # Generar pagos automáticos cada 15 días (id_pago autogenerado)
                fecha_pago = date.today()
                for _ in range(datos_credito['plazo_meses']):
                    cur.execute("""
                        INSERT INTO pagos (
                            id_usuario, fecha_pago, monto, estado_pago
                        ) VALUES (%s, %s, %s, %s)
                    """, (
                        self.id,
                        fecha_pago,
                        datos_credito['pago_mensual'],
                        'pendiente'
                    ))

                    fecha_pago += timedelta(days=15)

                current_app.logger.info(f"Usuario creado con ID {self.id}, crédito y pagos generados.")

        except UsuarioError:
            raise
        except Exception as e:
            current_app.logger.error(f"Error en guardar: {str(e)}")
            raise UsuarioError("Error técnico al registrar el usuario")
        

    @classmethod
    def consultar_por_id(cls, id):
        with pgdb.get_cursor() as cur:
            cur.execute("""
                SELECT id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena
                FROM usuarios
                WHERE id = %s
            """, (id,))
            row = cur.fetchone()
            if row:
                return cls(
                    id=row[0],
                    nombre=row[1],
                    apellido_paterno=row[2],
                    apellido_materno=row[3],
                    edad=row[4],
                    ingreso_mensual=row[5],
                    usuario=row[6],
                    contrasena=row[7],
                    #validar=False  # Metodo para no validar al Pagos en eliminarcion
                )
            return None
        

    @classmethod
    def actualizar(cls, id, nombre, apellido_paterno, apellido_materno, edad, contrasena):
        with pgdb.get_cursor() as cur:
            query = """
                UPDATE usuarios
                SET nombre = %s,
                    apellido_paterno = %s,
                    apellido_materno = %s,
                    edad = %s,
                    contrasena = %s
                WHERE id = %s
            """
            valores = (nombre, apellido_paterno, apellido_materno, edad, contrasena, id)
            cur.execute(query, valores)
            cur.connection.commit() 

    '''    
    @classmethod
    def actualizar(cls, id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena):
        with pgdb.get_cursor() as cur:
            query = """
                UPDATE usuarios
                SET nombre = %s,
                    apellido_paterno = %s,
                    apellido_materno = %s,
                    edad = %s,
                    ingreso_mensual = %s,
                    usuario = %s,
                    contrasena = %s
                WHERE id = %s
            """
            valores = (nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena, id)
            cur.execute(query, valores)
            cur.connection.commit() 
            '''


    @property
    def db(self):
        """Accede a la conexion global de la base de datos"""
        global pgdb
        if pgdb is None:
            raise DBException("La conexion a la base de datos no ha sido inicializada")
        return pgdb
    

    @classmethod
    def calcular_credito(cls, ingreso_mensual: float) -> Dict[str, Any]:
        if not ingreso_mensual or ingreso_mensual <= 0:
            raise UsuarioError("Ingreso mensual no válido")

        # Convertir ingreso a Decimal con dos decimales
        try:
            ingreso = Decimal(str(ingreso_mensual)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            #print(f"Ingreso mensual validado: {ingreso}")
        except:
            raise UsuarioError("Formato de ingreso inválido")

        # Validar rango mínimo de ingreso para aprobar crédito
        if not (Decimal('1799.99') < ingreso <= Decimal('99999.99')):
            raise UsuarioError("Crédito no aprobado")


        # Determinar tasa de interés basada en ingreso mensual
        # ○ 10% mensual para ingresos < 10,000 MXN 
        # ○ 8% mensual para ingresos entre 10,000 y 20,000 MXN 
        # ○ 6% mensual para ingresos > 20,000 MXN
            
        if ingreso < Decimal('10000.00'):
            tasa = Decimal('0.10')  # 10%
        elif Decimal('10000.00') <= ingreso <= Decimal('20000.00'):
            tasa = Decimal('0.08')  # 8%
        else:
            tasa = Decimal('0.06')  # 6%

        #print(f"Tasa de interés asignada: {tasa * 100}%")

        # Calcular el monto del crédito (sujeto a un máximo de 2 veces el ingreso)
        #monto_credito = (ingreso * Decimal('2')).quantize(Decimal('0.01'))
        monto_credito = (ingreso * Decimal('0.3')).quantize(Decimal('0.01'))
        monto_credito = (monto_credito*12)
        #print(f"Monto crédito calculado: {monto_credito}")

        total_credito_con_interes = (monto_credito * (Decimal('1') + tasa)).quantize(Decimal('0.01'))

        pago_maximo = (ingreso * Decimal('0.30')).quantize(Decimal('0.01'))
        meses = 1
        while meses <= 12:
            pago_mensual = (total_credito_con_interes / Decimal(meses)).quantize(Decimal('0.01'))
            if pago_mensual <= pago_maximo:
                break
            meses += 1

        if meses > 12:
            meses = 12
            pago_mensual = (total_credito_con_interes / Decimal('12')).quantize(Decimal('0.01'))


        return {
            "monto_credito": float(monto_credito),
            "tasa_interes": float(tasa),
            "plazo_meses": meses,
            "pago_mensual": float(pago_mensual),
            "total_credito_con_interes": float(total_credito_con_interes),
            "Mensaje": "Crédito aprobado"
        }

    '''
    @classmethod
    def calcular_credito(cls, ingreso_mensual: float) -> Dict[str, Any]:
       
        if not ingreso_mensual or ingreso_mensual <= 0:
            raise UsuarioError("Ingreso mensual no válido")

        try:
            ingreso = Decimal(str(ingreso_mensual)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            raise UsuarioError("Formato de ingreso inválido")

        # Lógica de cálculo
        if ingreso < Decimal('10000'):
            tasa = Decimal('0.10')
        elif ingreso < Decimal('20000'):
            tasa = Decimal('0.08')
        else:
            tasa = Decimal('0.06')

        monto_credito = min(max(ingreso * 10, Decimal('1000')), Decimal('100000'))
        total_credito_con_interes = monto_credito * (1 + tasa)
        
        # Cálculo de plazo
        pago_max = ingreso * Decimal('0.30')
        meses = 1
        while (total_credito_con_interes / meses) > pago_max:
            meses += 1

        return {
            "monto_credito": float(monto_credito.quantize(Decimal('0.01'))),
            "tasa_interes": float(tasa),
            "plazo_meses": meses,
            "pago_mensual": float((total_credito_con_interes / meses).quantize(Decimal('0.01'))),
            "total_credito_con_interes": float(total_credito_con_interes.quantize(Decimal('0.01')))
        }
        '''
    '''
    @classmethod
    def eliminar(cls, id_usuario):
        """
        Elimina un usuario por su ID.
        """
        try:
            with pgdb.get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
        except Exception as e:
            current_app.logger.error(f"Error eliminando usuario con ID {id_usuario}: {e}")
            raise UsuarioError("Error técnico al intentar eliminar el usuario.")
            '''


    @classmethod
    def eliminar_usuario_cascade(cls, id_usuario):
        """
        Elimina en cascada los pagos, el crédito y el registro del usuario,
        **solo** si todos sus pagos están en 'Pagado'.
        """
        # 1) Validar primero
        Pago.validar_todos_pagados(id_usuario)

        try:
            with pgdb.get_cursor(commit=True) as cur:
                # Eliminar pagos
                cur.execute("DELETE FROM pagos WHERE id_usuario = %s", (id_usuario,))
                # Eliminar crédito
                cur.execute("DELETE FROM creditos WHERE id_usuario = %s", (id_usuario,))
                # Eliminar usuario
                cur.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
        except Exception as e:
            current_app.logger.error(f"Error eliminando datos del usuario {id_usuario}: {e}")
            raise UsuarioError("Error técnico al eliminar el usuario.")
    
class Pago:
    def __init__(self, linea_captura=None, validar=True):
        if validar:
           if not linea_captura or not re.fullmatch(r"\d{15}", linea_captura):
                raise PagoError("La línea de captura debe contener exactamente 15 dígitos numéricos")

        self.linea_captura = linea_captura
    
    @classmethod
    def PagoExitoso(cls, id_pago, nuevo_estado):
        
        try:
            with pgdb.get_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE pagos SET estado_pago = %s WHERE id_pago = %s""", (nuevo_estado, id_pago))
        except Exception as e:
            current_app.logger.error(f"Error al actualizar estado del pago {id_pago}: {e}")
            raise PagoError("Error técnico al actualizar el estado del pago")
        

    @classmethod
    def PagoExitoso_usuario(cls, id_usuario, nuevo_estado):
        """Marca todos los pagos de un usuario como pagados."""
        try:
            with pgdb.get_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE pagos
                    SET estado_pago = %s
                    WHERE id_usuario = %s
                """, (nuevo_estado, id_usuario))
        except Exception as e:
            current_app.logger.error(f"Error al actualizar pagos del usuario {id_usuario}: {e}")
            raise PagoError("Error técnico al actualizar el estado de los pagos")
        

    @classmethod
    def validar_todos_pagados(cls, id_usuario):
        """
        Verifica que no existan pagos pendientes para el usuario.
        Lanza PagoError si hay algún pago con estado distinto de 'Pagado'.
        """
        try:
            with pgdb.get_cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM pagos 
                    WHERE id_usuario = %s AND estado_pago <> 'Pagado'
                """, (id_usuario,))
                pendientes = cur.fetchone()[0]
                if pendientes > 0:
                    raise PagoError("No todos los pagos están en estado 'Pagado'.")
        except PagoError:
            raise
        except Exception as e:
            current_app.logger.error(f"Error validando pagos de usuario {id_usuario}: {e}")
            raise PagoError("Error técnico al validar estado de pagos.")

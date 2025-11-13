import pytest
from app_web.sistema import create_app
from app_web.extension  import pgdb 
from app_web.models import Usuario, UsuarioError, Pago, PagoError
from decimal import Decimal, ROUND_HALF_UP
from flask import current_app

def eliminar():
    with pgdb.get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM usuarios")
   

# ----------------------------
# Pruebas para la clase Pago
# ----------------------------
app = create_app()
app.config.update({
        "TESTING": True,
    })

@pytest.mark.parametrize(
    "id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena",
    [
        (None, "A"*5, "A"*5, "A"*5, 30, 60000.00, "A"*5, "1234"),
    ]
)

def test_crear_usuario_correctamente(id, nombre, apellido_paterno,apellido_materno,edad,ingreso_mensual, usuario, contrasena):
    us = Usuario(id,nombre, apellido_paterno,apellido_materno,edad,ingreso_mensual, usuario, contrasena)
    assert us.id == id
    assert us.nombre == nombre
    assert us.apellido_paterno == apellido_paterno
    assert us.apellido_materno == apellido_materno
    assert us.edad == edad
    assert us.ingreso_mensual == ingreso_mensual
    assert us.usuario == usuario
    assert us.contrasena == contrasena


@pytest.mark.parametrize(
    "id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena, validar, valor_esperado",
    [
        # Campos vacíos uno a uno
        (None, '', "A"*5, "A"*5, 30, 10000.0, "A"*5, "1234", True, UsuarioError),  # nombre vacío
        (None, "A"*5, '', "A"*5, 30, 10000.0, "A"*5, "1234", True, UsuarioError),  # apellido_paterno vacío
        (None, "A"*5, "A"*5, '', 30, 10000.0, "A"*5, "1234", True, UsuarioError),  # apellido_materno vacío

        # Edad fuera de rango
        (None, "A"*5, "A"*5, "A"*5, 10, 10000.0, "A"*5, "1234", True, UsuarioError),

        # Ingreso mensual negativo
        (None, "A"*5, "A"*5, "A"*5, 30, -10000.0, "A"*5, "1234", True, UsuarioError),

        # Usuario demasiado largo
        (None, "A"*5, "A"*5, "A"*5, 30, 10000.0, "usuario_muy_largo123456789", "1234", True, UsuarioError),

        # Contraseña demasiado corta
        (None, "A"*5, "A"*5, "A"*5, 30, 10000.0, "A"*5, "12", True, UsuarioError),
    ]
)
def test_instancia_usuarios_errores(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena, validar, valor_esperado):
    with pytest.raises(valor_esperado):
        Usuario(
            id=id,
            nombre=nombre,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            edad=edad,
            ingreso_mensual=ingreso_mensual,
            usuario=usuario,
            contrasena=contrasena,
            validar=validar
        )
# --------------------------------------------------
def test_consultar_usuarios_correctamente():
    with app.app_context():
        id = None
        nombre = 'A'*5
        apellido_paterno = 'A'*5
        apellido_materno = 'A'*5
        edad = 30
        ingreso_mensual = 10000
        usuario = 'A'*5
        contrasena = "1234"
        us = Usuario(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena)
        us.guardar()
        resultado = Usuario.consultar_usuario(usuario)
        assert resultado.nombre == nombre
       

def test_consultar_usuarios_incorrectamente():
    with app.app_context():
        id = None
        nombre = 'B'*5
        apellido_paterno = 'B'*5
        apellido_materno = 'B'*5
        edad = 30
        ingreso_mensual = 10000
        usuario = 'B'*5
        contrasena = "1234"
        us = Usuario(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena)
        us.guardar()
        usuario_error= 'C'*5  # Usuario que no existe
        resultado = Usuario.consultar_usuario(usuario_error)
        assert resultado == None
        

def test_usuario_ya_existente():
     with app.app_context():
        id = None
        nombre = 'A'*5
        apellido_paterno = 'A'*5
        apellido_materno = 'A'*5
        edad = 30
        ingreso_mensual = 10000
        usuario = 'A'*5
        contrasena = "1234"
        us = Usuario(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena)
        with pytest.raises(UsuarioError) as e:
            us.guardar()

def test_verificar_credenciales():
     with app.app_context():
        id = None
        nombre = 'D'*5
        apellido_paterno = 'D'*5
        apellido_materno = 'D'*5
        edad = 30
        ingreso_mensual = 10000
        usuario = 'D'*5
        contrasena = "1234"
        us = Usuario(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena)
        us.guardar()
        DatosUsuario = Usuario.verificar_credenciales(usuario, contrasena)   
        assert DatosUsuario['usuario'] == us.usuario

def test_verificar_credenciales_incorrectas():
     with app.app_context():
        id = None
        nombre = 'E'*5
        apellido_paterno = 'E'*5
        apellido_materno = 'E'*5
        edad = 30
        ingreso_mensual = 10000
        usuario = 'E'*5
        contrasena = "1234"
        contrasenia_erronea= "4321"
        us = Usuario(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena)
        us.guardar()
        DatosUsuario = Usuario.verificar_credenciales(usuario, contrasenia_erronea)   
        assert DatosUsuario == None


'''
def test_calcular_credito_ingreso_menor_20000():
        ingreso = 19000.00
        monto_credito = 38000.00
        tasa_interes = 0.08
        plazo_meses = 8
        pago_mensual = 5130.00
        totalcredito = 41040.00
        resultado = Usuario.calcular_credito(ingreso)
        assert resultado['monto_credito'] == monto_credito
        assert resultado['tasa_interes'] == tasa_interes
        assert resultado['plazo_meses'] == plazo_meses
        assert resultado['pago_mensual'] == pago_mensual
        assert resultado['total_credito_con_interes'] == totalcredito

def test_calcular_credito_ingreso_mayor_20000():
        ingreso = 3000.00 
        monto_credito = 6000.00
        tasa_interes = 0.10
        plazo_meses = 8
        pago_mensual = 825.00
        totalcredito = 6600.00
        resultado = Usuario.calcular_credito(ingreso)
 
        assert resultado['monto_credito'] == monto_credito
        assert resultado['tasa_interes'] == tasa_interes
        assert resultado['plazo_meses'] == plazo_meses
        assert resultado['pago_mensual'] == pago_mensual
        assert resultado['total_credito_con_interes'] == totalcredito
        '''

def test_calcular_credito_ingreso_menor():       
        ingreso = 1000.0
        with pytest.raises(UsuarioError) as e:
            resultado = Usuario.calcular_credito(ingreso)
        
def test_Limpiar():
    eliminar()

@pytest.mark.parametrize("linea", [
    ("123456789012345"),   # 15 dígitos válidos → OK              
])
def test_pago_Exitoso(linea):
        p = Pago(linea)
        assert p.linea_captura == linea

@pytest.mark.parametrize("linea, debe_fallar", [
    ("123456789012345", False),   # 15 dígitos válidos → OK
    ("", True),                   # vacío → error
    ("123", True),                # muy corto → error
    ("1" * 14 + "A", True),       # caracteres no numéricos → error
    ("1" * 16, True),             # muy largo → error
])
def test_pago_init(linea, debe_fallar):
    if debe_fallar:
        with pytest.raises(PagoError):
            Pago(linea)
    else:
        p = Pago(linea)
        assert p.linea_captura == linea

# --------------------------------------------------
# Pruebas para Usuario.calcular_credito (casos borde)
# --------------------------------------------------
'''
@pytest.mark.parametrize("ingreso, esperado", [
    # Ingreso < 10000 → tasa 10%, monto=ingreso*2, total=ingreso*2*1.1, plazo=8
    (9000.0, {
        'monto_credito': 18000.00,
        'tasa_interes':  0.10,
        'plazo_meses':   8,
        'pago_mensual':  round(19800.00 / 8, 2),  # 2475.00
        'total_credito_con_interes': 19800.00
    }),
    # Ingreso = 19000 → tasa 8%, monto=38000, total=41040, plazo=8
    (19000.0, {
        'monto_credito': 38000.00,
        'tasa_interes':  0.08,
        'plazo_meses':   8,
        'pago_mensual':  round(41040.00 / 8, 2),  # 5130.00
        'total_credito_con_interes': 41040.00
    }),
    # Ingreso = 30000 → tasa 6%, monto=60000, total=63600, plazo=8
    (30000.0, {
        'monto_credito': 60000.00,
        'tasa_interes':  0.06,
        'plazo_meses':   8,
        'pago_mensual':  round(63600.00 / 8, 2),  # 7950.00
        'total_credito_con_interes': 63600.00
    }),
])
def test_calcular_credito_casos_bordes(ingreso, esperado):
    resultado = Usuario.calcular_credito(ingreso)
    assert resultado['monto_credito']             == pytest.approx(esperado['monto_credito'], rel=1e-3)
    assert resultado['tasa_interes']              == pytest.approx(esperado['tasa_interes'],    rel=1e-3)
    assert resultado['plazo_meses']               == esperado['plazo_meses']
    assert resultado['pago_mensual']              == pytest.approx(esperado['pago_mensual'],   rel=1e-3)
    assert resultado['total_credito_con_interes'] == pytest.approx(esperado['total_credito_con_interes'], rel=1e-3)
'''


def test_calcular_credito_ingreso_no_valido():
    with pytest.raises(UsuarioError, match="Ingreso mensual no válido"):
        Usuario.calcular_credito(-500.0)

def test_calcular_credito_credito_fuera_rango_bajo():
    # ingreso*10 < 1000 → rechaza
    with pytest.raises(UsuarioError, match="Crédito no aprobado"):
        Usuario.calcular_credito(50.0)

def test_calcular_credito_credito_fuera_rango_alto():
    # ingreso >= 100000 → rechaza de entrada
    with pytest.raises(UsuarioError, match="Crédito no aprobado"):
        Usuario.calcular_credito(100000.0)
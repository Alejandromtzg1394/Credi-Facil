import pytest
import sys
from app_web.sistema import create_app
from app_web.extension  import pgdb 
from app_web.models import Usuario, UsuarioError, Pago, PagoError
from decimal import Decimal, ROUND_HALF_UP



# --------------------------------------------------
# Pruebas para Pago (ECP + Valores Límite)
# --------------------------------------------------
@pytest.mark.parametrize("linea_captura", [
    # T1 - caso válido
    ("1" * 15) 
    
])
def test_pago_Exitoso(linea_captura):
        pago = Pago(linea_captura)
        assert pago.linea_captura == linea_captura


@pytest.mark.parametrize("linea_captura", [
    
    # T6 - línea de captura vacía
    (""),
    
    # T7 - línea de captura corta
    ("2" * 7),
    
    # T8 - línea de captura larga
    ("2" * 20),
    
    # T9 - línea de captura alfanumérica
    ("ABC123XYZ456789"),
])
def test_linea_captura(linea_captura):
    with pytest.raises(PagoError, match="La línea de captura debe contener exactamente 15 dígitos numéricos"):
        Pago(linea_captura)
    



@pytest.mark.parametrize("linea_captura, debe_fallar, mensaje", [
    # T1: Línea con 15 caracteres alfabéticos (no numéricos) → inválido
    ("A"*15, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T2: Línea vacía → inválido
    ("", True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T3: Línea con 1 caracter alfabético → inválido (longitud incorrecta)
    ("A", True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T4: Línea con 2 caracteres alfabéticos → inválido (longitud incorrecta)
    ("AA", True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T5: Línea con 13 caracteres alfabéticos → inválido (longitud incorrecta)
    ("A"*13, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T6: Línea con 14 caracteres alfabéticos → inválido (longitud incorrecta)
    ("A"*14, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T7: Línea con 16 caracteres alfabéticos → inválido (longitud incorrecta)
    ("A"*16, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T8: Línea con 17 caracteres alfabéticos → inválido (longitud incorrecta)
    ("A"*17, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T9: Línea con 99 caracteres alfabéticos → inválido (longitud incorrecta)
    ("A"*99, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T10: Línea con 100 caracteres alfabéticos → inválido (longitud incorrecta)
    ("A"*100, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T11: Línea con 101 caracteres alfabéticos → inválido (longitud incorrecta)
    ("A"*101, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T12: Línea con 15 caracteres alfanuméricos (mezcla de letras y números) → inválido
    ("A1B2C3D4E5F6G7H", True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T13: Línea con 15 caracteres alfabéticos, y otra línea vacía → inválido (simulando dos folios)
    # Como sólo prueba un campo, se evalúa el vacío → inválido
    ("", True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T14: Línea con 15 caracteres alfabéticos, y otra línea con 1 caracter alfabético → inválido
    ("A", True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T15: Línea con 15 caracteres alfabéticos, y otra línea con 2 caracteres alfabéticos → inválido
    ("AA", True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T16: Línea con 15 caracteres alfabéticos, y otra línea con 13 caracteres alfabéticos → inválido
    ("A"*13, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T17: Línea con 15 caracteres alfabéticos, y otra línea con 14 caracteres alfabéticos → inválido
    ("A"*14, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T18: Línea con 15 caracteres alfabéticos, y otra línea con 16 caracteres alfabéticos → inválido
    ("A"*16, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T19: Línea con 15 caracteres alfabéticos, y otra línea con 17 caracteres alfabéticos → inválido
    ("A"*17, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T20: Línea con 15 caracteres alfabéticos, y otra línea con 99 caracteres alfabéticos → inválido
    ("A"*99, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T21: Línea con 15 caracteres alfabéticos, y otra línea con 100 caracteres alfabéticos → inválido
    ("A"*100, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T22: Línea con 15 caracteres alfabéticos, y otra línea con 101 caracteres alfabéticos → inválido
    ("A"*101, True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # T23: Línea con 15 caracteres alfabéticos, y otra línea con 15 caracteres alfanuméricos → inválido
    ("A1B2C3D4E5F6G7H", True, "La línea de captura debe contener exactamente 15 dígitos numéricos"),
    
    # Caso válido para control (15 dígitos numéricos)
    ("123456789012345", False, ""),
])
def test_pago_init_parametrizado(linea_captura, debe_fallar, mensaje):
    if debe_fallar:
        with pytest.raises(PagoError, match=mensaje):
            Pago(linea_captura)
    else:
        pago = Pago(linea_captura)
        assert pago.linea_captura == linea_captura



# Casos de prueba válidos y rechazados según la tabla ECP y valores límite
'''
@pytest.mark.parametrize("id,nombre,apellido_paterno, apellido_materno,edad,ingreso_mensual,usuario,contrasena", [
    # T1 - Caso válido, crédito aceptado
    (None,"A"*13, "A"*13, "A"*13, 35, 50000.0, "A"*7, "1"*4),

])

def test_usuario_credito_aceptado_y_denegado(id,nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena):
    UsuarioTest = Usuario(id,nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena)
    assert UsuarioTest.calcular_credito(ingreso_mensual) == {"monto_credito": 180000.00,"tasa_interes": 0.06,"plazo_meses": 12,"pago_mensual": 15900.00,"total_credito_con_interes": 190800.00}
    '''

@pytest.mark.parametrize("id,nombre,apellido_paterno, apellido_materno,edad,ingreso_mensual,usuario,contrasena, mensaje_esperado", [
    # T1 - Caso válido, crédito aceptado
    (None,"A"*13, "A"*13, "A"*13, 35, 50000.0, "A"*7, "1"*4,"Crédito aprobado"),

])

def test_usuario_credito_aceptado_y_denegado(id,nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena,mensaje_esperado):
    UsuarioTest = Usuario(id,nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena)
    resultado = UsuarioTest.calcular_credito(ingreso_mensual)
    assert resultado["Mensaje"]== str(mensaje_esperado)
    

@pytest.mark.parametrize("id,nombre,apellido_paterno, apellido_materno,edad,ingreso_mensual,usuario,contrasena, tipo, mensaje_esperado", [
    # Crédito Denegado
    (None, "A"*13, "A"*13, "A"*13, 9, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "A"*13, "A"*13, 35, 1000, "A"*7, "1"*4, None , "Crédito no aprobado"),
    (None, "A"*13, "A"*13, "A"*13, 35, 7000000, "A"*7, "1"*4, None, "Crédito no aprobado"),

    # Errores de campo vacío
    (None, "", "A"*13, "A"*13, 35, 50000.0, "A"*7, "1"*4,"Usuario", UsuarioError),
    (None, "A"*13, "", "A"*13, 35, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "A"*13, "", 35, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "A"*13, "A"*13, -10, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "A"*13, "A"*13, 35, -50, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "A"*13, "A"*13, 35, 50000.0, "", "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "A"*13, "A"*13, 35, 50000.0, "A"*7, "", "Usuario", UsuarioError),

    # Errores de campo inválido (longitudes o caracteres incorrectos)
    (None, "A"*50, "A"*13, "A"*13, 35, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "A"*50, "A"*13, 35, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),    
    (None, "A"*13, "A"*13, "A"*50, 35, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "1234567890123", "A"*13, "A"*13, 35, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "1234567890123", "A"*13, 35, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "A"*13, "1234567890123", 35, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "A"*13, "A"*13, 80, 50000.0, "A"*7, "1"*4, "Usuario", UsuarioError),
    (None, "A"*13, "A"*13, "A"*13, 35, 50000.0, "@@@@", "1"*4, "Usuario", UsuarioError),
])
def test_usuario_credito_denegado_o_error(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena, tipo, mensaje_esperado):

    if tipo == "Usuario":
        with pytest.raises(mensaje_esperado):
            Usuario(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena)
    else:
        with pytest.raises(UsuarioError) as exc_info:
             resultado = Usuario(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena).calcular_credito(ingreso_mensual)
        assert mensaje_esperado in str(exc_info.value)
# --------------------------------------------------

@pytest.mark.parametrize("id,nombre,apellido_paterno, apellido_materno,edad,ingreso_mensual,usuario,contrasena, tipo, mensaje_esperado", [
    # Crédito Denegado
    (None, "A", "A", "A", 18, 1800.0, "U", "1"*4, None, "Crédito aprobado"),
    (None, "A"*2, "A"*2, "A"*2, 19, 1800.1, "U"*2, "1"*4, None, "Crédito aprobado"),
    (None, "A"*24, "A"*24, "A"*24, 64, 99999.99, "U"*14, "1"*4, None, "Crédito aprobado"),
    (None, "A"*24, "A"*24, "A"*24, 64, 99998.99, "U"*14, "1"*4, None, "Crédito aprobado"),

    (None, "A"*24, "A"*24, "A"*24, 19, 0.1, "U"*14, "1"*4, "Credito", "Crédito no aprobado"),
    (None, "A"*24, "A"*24, "A"*24, 19, 0.2, "U"*14, "1"*4, "Credito", "Crédito no aprobado"),
    (None, "A"*24, "A"*24, "A"*24, 19, 1799.9, "U"*14, "1"*4, "Credito", "Crédito no aprobado"),

    #(None, "A"*24, "A"*24, "A"*24, 19, 0.1, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 1, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 2, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 16, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 17, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    
    (None, "",     "A"*24, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "B"*26,  "A"*24, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "C"*27,  "A"*24, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "D"*99,  "A"*24, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "E"*100, "A"*24, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "F"*101, "A"*24, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),

    (None, "A"*24,  "", "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "B"*26, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "C"*27, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "D"*99, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "E"*100, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "F"*101, "A"*24, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),

    (None, "A"*24,  "A"*24, "", 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "B"*26, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "C"*27, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "D"*99, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "E"*100, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "F"*101, 19, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),

    (None, "A"*24,  "A"*24, "A"*24, -sys.maxsize, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "A"*24, -2, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "A"*24, -1, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "A"*24, 0, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "A"*24, 66, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "A"*24, 67, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24,  "A"*24, "A"*24, sys.maxsize, 1800.0, "U"*14, "1"*4, "Usuario", UsuarioError),

    (None, "A"*24, "A"*24, "A"*24, 19, -sys.maxsize, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 19, -0.1, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 19, 0, "U"*14, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 19, 1000000.00, "U"*14, "1"*4, "Credito", "Crédito no aprobado"),
    (None, "A"*24, "A"*24, "A"*24, 19, 1000000.01, "U"*14, "1"*4, "Credito", "Crédito no aprobado"),

    (None, "A"*24, "A"*24, "A"*24, 1, 1800.0, "", "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 2, 1800.0, "U"*16, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 16, 1800.0, "U"*17, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 17, 1800.0, "U"*99, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 17, 1800.0, "U"*100, "1"*4, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 17, 1800.0, "U"*101, "1"*4, "Usuario", UsuarioError),

    (None, "A"*24, "A"*24, "A"*24, 1, 1800.0, "U"*14, "", "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 2, 1800.0, "U"*14, "1"*1, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 16, 1800.0, "U"*14, "1"*3, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 17, 1800.0, "U"*14, "1"*5, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 17, 1800.0, "U"*14, "1"*6, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 17, 1800.0, "U"*14, "1"*99, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 17, 1800.0, "U"*14, "1"*100, "Usuario", UsuarioError),
    (None, "A"*24, "A"*24, "A"*24, 17, 1800.0, "U"*14, "1"*101, "Usuario", UsuarioError),

])
def test_VALORES_LIMITE_DE_3(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena, tipo, mensaje_esperado):

    if tipo == "Usuario":
        with pytest.raises(mensaje_esperado):
            Usuario(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena)
    elif tipo == "Credito":
        with pytest.raises(UsuarioError) as exc_info:
            resultado = Usuario(id, nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena).calcular_credito(ingreso_mensual)
        assert mensaje_esperado in str(exc_info.value)
    else:
        UsuarioTest = Usuario(id,nombre, apellido_paterno, apellido_materno, edad, ingreso_mensual, usuario, contrasena)
        resultado = UsuarioTest.calcular_credito(ingreso_mensual)
        assert resultado["Mensaje"]== str(mensaje_esperado)


-- Crear base de datos
CREATE DATABASE credi_facil;

-- (IMPORTANTE: este bloque se ejecuta en una sesión aparte conectada a 'credi_facil')

-- Tabla: usuarios
CREATE TABLE usuarios (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100) NOT NULL,
    edad INTEGER NOT NULL,
    ingreso_mensual NUMERIC(10,2) NOT NULL,
    usuario VARCHAR(20) UNIQUE NOT NULL,
    contrasena VARCHAR(100) NOT NULL
);

-- Tabla: creditos
CREATE TABLE creditos (
    id_credito INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    monto_credito NUMERIC(10,2) NOT NULL,
    tasa_interes NUMERIC(5,4) NOT NULL,
    plazo_meses INTEGER NOT NULL,
    pago_mensual NUMERIC(10,2) NOT NULL,
    total_con_interes NUMERIC(10,2) NOT NULL
);

-- Tabla: pagos
CREATE TABLE pagos (
    id_pago INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    fecha_pago DATE NOT NULL,
    monto NUMERIC(10,2) NOT NULL,
    estado_pago VARCHAR(20) NOT NULL
);
-- Tabla: historial_creditos
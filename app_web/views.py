from flask import render_template, request, redirect, url_for, session, flash, jsonify

from .models import Usuario, UsuarioError
from .models import Pago, PagoError
from .extension import pgdb  

_ingreso_almacenado = None


# Datos de usuarios (simulados para el ejemplo)
USUARIOS = {
    'usuario1': 'u1',
    'usuario2': 'u2'
}

def registrar_rutas(app):

    #----------------------------------------
    # Registro de la clave secreta para el uso de sesiones del usuario
    #---------------------------------------- 
    SECRET_KEY='2ca8efd458259a5de5d4c2ce5692475d31401923470d34b1b6b86055453b5488017858b6351e4bd8615e7cf669cdb63e170d792865c04846cb06e6aa48f82b7f'
    app.config['SECRET_KEY'] = SECRET_KEY



    # Inicio de sesión
    @app.route('/', methods=['GET'])
    @app.route('/inicio', methods=['GET'])
    def inicio_home():
        _ingreso_almacenado = None
        return render_template('inicio.html')


    @app.route('/login', methods=['GET', 'POST'])
    def login_home():
        if 'usuario' in session:
            flash('Ya has iniciado sesión', 'info')
            return redirect(url_for('perfil'))

        if request.method == 'POST':
            usuario = request.form.get('usuario')
            contrasena = request.form.get('contrasena')

            DatosUsuario = Usuario.verificar_credenciales(usuario, contrasena)

            if DatosUsuario:
                session['usuario_id'] = DatosUsuario['id']
                session['usuario'] = DatosUsuario['usuario']
                print(f"Usuario {session['usuario']} ha iniciado sesión")
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('perfil'))
            else:
                flash('Credenciales inválidas', 'danger')

        return render_template('login.html')
        



    @app.route('/logout')
    def logout():
        session.clear()
        _ingreso_almacenado = None
        flash("Sesión cerrada correctamente", 'success')
        return redirect(url_for('inicio_home'))

    @app.route('/registro', methods=['GET', 'POST'])
    def registro():
        if 'usuario' in session:
            flash('Ya has iniciado sesión', 'info')
            return redirect(url_for('perfil'))
         
        global _ingreso_almacenado

        if _ingreso_almacenado is not None:

            ingreso_cotizado = _ingreso_almacenado
        else:
            ingreso_cotizado = 0.0
        
        form_data = {}
        errores = {}

        if request.method == 'POST':
            try:
                # Recoger y validar datos
                form_data = {
                    'nombre': request.form['nombre'].strip(),
                    'apellido_paterno': request.form['apellido_paterno'].strip(),
                    'apellido_materno': request.form['apellido_materno'].strip(),
                    'edad': int(request.form['edad']),
                    'ingreso': float(request.form['ingreso']),
                    'usuario': request.form['usuario'].strip().lower(),
                    'contrasena': request.form['contrasena']
                }

                nuevo_usuario = Usuario(
                    nombre=form_data['nombre'],
                    apellido_paterno=form_data['apellido_paterno'],
                    apellido_materno=form_data['apellido_materno'],
                    edad=form_data['edad'],
                    ingreso_mensual=form_data['ingreso'],
                    usuario=form_data['usuario'],
                    contrasena=form_data['contrasena'],  
                )
                
                nuevo_usuario.guardar()
                _ingreso_almacenado=None

                flash('¡Registro exitoso! Por favor inicia sesión', 'success')
                return redirect(url_for('login_home'))

            except KeyError as e:
                flash(f'Campo obligatorio faltante: {e}', 'danger')
            except ValueError as e:
                flash('Error en formato numérico', 'danger')
            except UsuarioError as e:
                flash(str(e), 'danger')
            except Exception as e:
                app.logger.error(f'Error en registro: {str(e)}')
                flash('Error interno. Intente nuevamente', 'danger')

        return render_template('registro.html',
                            form_data=form_data,
                            ingreso=ingreso_cotizado,
                            errores=errores)
    


    @app.route('/consulta_credito', methods=['GET', 'POST'])
    def consulta_credito():
        global _ingreso_almacenado
        _ingreso_almacenado = None
        resultado = None
        error = None
        ingreso = None

        if request.method == 'POST':
            try:
                ingreso_str = request.form['ingreso']
                ingreso_str = ingreso_str.replace(',', '')  # elimina comas de miles
                ingreso = float(ingreso_str)


                _ingreso_almacenado = ingreso  # Almacena el ingreso globalmente si es necesario
                ingreso_mensual(ingreso)       # Llama tu lógica adicional
                resultado = Usuario.calcular_credito(ingreso)  # Llama el cálculo

            except ValueError:
                error = "Ingrese un valor numérico válido."
            except UsuarioError as e:
                error = str(e)
            except Exception as e:
                error = "Error inesperado en el cálculo."
                app.logger.error(f'Error en consulta crédito: {str(e)}')

        return render_template('consulta_credito.html',
                            resultado=resultado,
                            error=error,
                            ingreso=ingreso)




    @app.route('/perfil')
    def perfil():
        if 'usuario' not in session:
            flash('No se ha iniciado sesión', 'danger')
            return redirect(url_for('login_home'))

        usuario_nombre = session['usuario']
        usuario = Usuario.consultar_usuario(usuario_nombre)

        if not usuario:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('login_home'))

        pagos = Usuario.consultar_pagos(usuario.id)

        return render_template("perfil.html", 
            datos=[usuario], datoscredito=[usuario.credito], pagos=pagos)
    

    @app.route('/pagar_pago/<int:id>', methods=['GET', 'POST'])
    def pagar_pago(id):
        if request.method == 'POST':
            linea_captura = request.form.get('linea_captura')
            try:
                pago = Pago(linea_captura=linea_captura)  # Validación automática
                Pago.PagoExitoso(id_pago=id, nuevo_estado='Pagado')
                flash("El pago se ha registrado exitosamente.", "success")
                return redirect(url_for('perfil'))  # <-- Cambia esto según tu vista existente
            except PagoError as e:
                flash(str(e), "danger")
                

        return render_template('pagar_pago.html', id_pago=id)
    

    @app.route('/pago_total/<int:id_usuario>', methods=['GET', 'POST'])
    def pago_total(id_usuario):
        # Verificar sesión
        if 'usuario' not in session:
            flash('Debes iniciar sesión para realizar el pago.', 'warning')
            return redirect(url_for('login_home'))

        if request.method == 'POST':
            linea_captura = request.form.get('linea_captura')
            try:
                # Validación de la línea de captura
                pago = Pago(linea_captura=linea_captura)
                # Actualizar todos los pagos del usuario
                Pago.PagoExitoso_usuario(id_usuario=id_usuario, nuevo_estado='Pagado')
                flash("Todos tus pagos se han registrado exitosamente.", "success")
                return redirect(url_for('perfil'))
            except PagoError as e:
                flash(str(e), "danger")
            except Exception:
                flash("Ocurrió un error inesperado al procesar el pago.", "danger")

        # GET o POST con error: mostramos el formulario de línea de captura
        return render_template('pagar_pago.html', id_usuario=id_usuario)
    

    @app.route('/editar/<int:id>', methods=['GET', 'POST'])
    def editar_usuario(id):
        print("---->Editando")
        usuario_existente = Usuario.consultar_por_id(id)
        print(usuario_existente)

        if request.method == 'POST':
            print("---->Entro")
            try:
                nombre = request.form['nombre'].strip() 
                print(nombre)
                apellido_paterno = request.form['apellido_paterno'].strip()
                print(apellido_paterno)
                apellido_materno = request.form['apellido_materno'].strip()
                print(apellido_materno)
                edad = int(request.form['edad'])
                print(edad)
                '''
                ingreso_mensual = float(request.form['ingreso_mensual'])
                print(ingreso_mensual)
                '''
                contrasena = request.form['contrasena']
                print(contrasena)
                

                # Validación reutilizando constructor
                usuario_actualizado = Usuario(
                    nombre=nombre,
                    apellido_paterno=apellido_paterno,
                    apellido_materno=apellido_materno,
                    edad=edad,
                    ingreso_mensual=usuario_existente.ingreso_mensual,
                    usuario=usuario_existente.usuario,
                    contrasena=contrasena
                )

                
                Usuario.actualizar(
                    id=id,
                    nombre=nombre,
                    apellido_paterno=apellido_paterno,
                    apellido_materno=apellido_materno,
                    edad=edad,
                    #ingreso_mensual=ingreso_mensual,
                    #usuario=usuario_existente.usuario,
                    contrasena=contrasena
                )

                flash("Usuario actualizado correctamente", "success")
                return redirect(url_for('perfil'))

            except ValueError:
                flash("Error en formato numérico. Verifica edad o ingreso.", "danger")
            except UsuarioError as e:
                flash(f"Error en validación: {str(e)}", "danger")
            except Exception as e:
                flash(f"Error interno: {str(e)}", "danger")

        return render_template('editar_usuario.html', usuario=usuario_existente)
    

    @app.route('/eliminar_usuario/<int:id>', methods=['GET'])
    def eliminar_usuario(id):
        # 1) Verificar sesión
        if 'usuario' not in session:
            flash('Debes iniciar sesión para eliminar tu cuenta.', 'warning')
            return redirect(url_for('login_home'))

        # 2) Intentar eliminación en cascada
        try:
            Usuario.eliminar_usuario_cascade(id_usuario=id)
            # 3) Si todo salió bien, limpiar sesión y confirmar
            session.clear()
            flash('Tu cuenta y todos tus datos han sido eliminados.', 'success')
            return redirect(url_for('inicio_home'))

        except PagoError:
            # Hay pagos pendientes: redirijo a “pago_total” para que liquide todo
            flash('Primero debes liquidar todos tus pagos antes de eliminar tu cuenta.', 'info')
            return redirect(url_for('pago_total', id_usuario=id))

        except UsuarioError as e:
            # Cualquier otro error en la eliminación
            flash(str(e), 'danger')
            return redirect(url_for('perfil'))



    @app.route('/microcredito')
    def microcredito():
        return render_template('microcredito.html')

    @app.route('/creditopersonal')
    def creditopersonal():
        return render_template('creditopersonal.html')

    @app.route('/creditoeducativo')
    def creditoeducativo():
        return render_template('creditoeducativo.html')
    
    

def ingreso_mensual(ingreso):
    global _ingreso_almacenado
    _ingreso_almacenado = ingreso
    return _ingreso_almacenado
    
    
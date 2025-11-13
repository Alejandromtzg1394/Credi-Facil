from flask import Flask, request, redirect, url_for, render_template
from .extension import pgdb
from .views import registrar_rutas

# Datos de usuarios (simulados para el ejemplo)
USUARIOS = {
    'usuario1': 'u1',
    'usuario2': 'u2'
}



def create_app():
    app = Flask(__name__)
    registrar_rutas(app)

    return app

app = create_app()
pgdb.init_app(app)


if __name__ == "__main__":
    app.run(debug=True)
    #app.run()


@app.template_filter('moneda')
def formato_moneda(valor):
    try:
        return "${:,.2f}".format(float(valor))
    except (ValueError, TypeError):
        return "$0.00"

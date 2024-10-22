import os
import ssl
import urllib.request
import json

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, jsonify, session)
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Cambia esto por una clave secreta segura
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

def allowSelfSignedHttps(allowed):
    # Omite la verificación del certificado del servidor en el cliente
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

allowSelfSignedHttps(True)  # Necesario si usas un certificado autofirmado en tu servicio

@app.route('/')
def index():
    print('Request for index page received')
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['GET', 'POST'])
def hello():
    options = ["Alertas proveedores", "Chat RIS", "indemnizables: seguimiento"]
    if request.method == 'POST':
        if 'name' in request.form and 'option' not in request.form:
            name = request.form.get('name')
            if name:
                print('Request for hello page received with name=%s' % name)
                return render_template('hello.html', name=name, options=options)
            else:
                print('Request for hello page received with no name or blank name -- redirecting')
                return redirect(url_for('index'))
        elif 'option' in request.form:
            name = request.form.get('name')
            selected_option = request.form.get('option')
            print('Option selected: %s' % selected_option)
            # Reiniciar historial de chat si se selecciona una nueva opción
            session.pop('chat_history', None)
            session.pop('seguimiento_chat_history', None)
            return render_template('hello.html', name=name, options=options, selected_option=selected_option)
    else:
        return redirect(url_for('index'))

@app.route('/promptflow', methods=['POST'])
def promptflow():
    data = request.get_json()
    # Obtener los campos del formulario
    periodo_actual = data.get('periodoArchivoActual', '')
    periodo_antiguo = data.get('periodoArchivoAntiguo', '')
    ruta_antiguo = data.get('rutaArchivoAntiguo', '')
    ruta_actual = data.get('rutaArchivoActual', '')

    # Preparar los datos para la solicitud
    payload = {
        "periodoArchivoActual": periodo_actual,
        "periodoArchivoAntiguo": periodo_antiguo,
        "rutaArchivoAntiguo": ruta_antiguo,
        "rutaArchivoActual": ruta_actual
    }

    body = str.encode(json.dumps(payload))

    url = os.getenv('ENDPOINT_1')
    api_key = os.getenv('KEY_1')

    if not api_key:
        return jsonify({'response': 'API key is missing'}), 500

    headers = {'Content-Type': 'application/json', 'Authorization': ('Bearer ' + api_key)}

    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)

        result = response.read()
        # Convertir bytes a string
        result_str = result.decode('utf-8')
        # Cargar el JSON
        result_json = json.loads(result_str)
        # Obtener el contenido de 'campo_output'
        campo_output = 'desarrollo'
        response_message = result_json.get(campo_output, 'No hay respuesta del API')

        return jsonify({'response': response_message})
    except urllib.error.HTTPError as error:
        print("La solicitud falló con el código de estado: " + str(error.code))
        print(error.info())
        error_message = error.read().decode("utf8", 'ignore')
        print(error_message)
        return jsonify({'response': 'Ocurrió un error: ' + error_message}), error.code

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')

    if message:
        # Obtener historial de chat de la sesión
        chat_history = session.get('chat_history', [])
        # Añadir el nuevo mensaje al historial
        chat_history.append({'inputs': {'question': message}})

        # Preparar los datos para la solicitud
        payload = {
            'question': message,
            'chat_history': chat_history[:-1]  # Enviar el historial sin el último mensaje
        }

        body = str.encode(json.dumps(payload))

        url = os.getenv('ENDPOINT_2')
        api_key = os.getenv('KEY_2')

        if not api_key:
            return jsonify({'response': 'API key is missing'}), 500

        headers = {'Content-Type': 'application/json', 'Authorization': ('Bearer ' + api_key)}

        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req)

            result = response.read()
            # Convertir el resultado a un diccionario de Python
            result_json = json.loads(result.decode('utf-8'))
            # Obtener la respuesta
            respuesta = result_json.get('answer', 'No hay respuesta del API')

            # Añadir la respuesta al historial
            chat_history[-1]['outputs'] = {'answer': respuesta}
            # Actualizar el historial en la sesión
            session['chat_history'] = chat_history

            return jsonify({'response': respuesta})
        except urllib.error.HTTPError as error:
            print("La solicitud falló con el código de estado: " + str(error.code))
            print(error.info())
            error_message = error.read().decode("utf8", 'ignore')
            print(error_message)
            return jsonify({'response': 'Ocurrió un error: ' + error_message}), error.code
    else:
        return jsonify({'response': 'No se recibió ningún mensaje'}), 400

@app.route('/seguimiento_chat', methods=['POST'])
def seguimiento_chat():
    data = request.get_json()
    message = data.get('message', '')
    numero_expediente = data.get('numeroExpediente', '')

    if message and numero_expediente:
        # Obtener historial de chat de la sesión
        chat_history = session.get('seguimiento_chat_history', {})
        expediente_history = chat_history.get(numero_expediente, [])

        # Añadir el nuevo mensaje al historial
        expediente_history.append({'inputs': {'question': message}})

        # Preparar los datos para la solicitud
        payload = {
            'question': message,
            'chat_history': expediente_history[:-1],  # Enviar el historial sin el último mensaje
            'numero expediente': numero_expediente
        }

        body = str.encode(json.dumps(payload))

        url = os.getenv('ENDPOINT_3')
        api_key = os.getenv('KEY_3')

        if not api_key:
            return jsonify({'response': 'API key is missing'}), 500

        headers = {'Content-Type': 'application/json', 'Authorization': ('Bearer ' + api_key)}

        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req)

            result = response.read()
            # Convertir el resultado a un diccionario de Python
            result_json = json.loads(result.decode('utf-8'))
            # Obtener la respuesta
            respuesta = result_json.get('answer', 'No hay respuesta del API')

            # Añadir la respuesta al historial
            expediente_history[-1]['outputs'] = {'answer': respuesta}

            # Actualizar el historial en la sesión
            chat_history[numero_expediente] = expediente_history
            session['seguimiento_chat_history'] = chat_history

            return jsonify({'response': respuesta})
        except urllib.error.HTTPError as error:
            print("La solicitud falló con el código de estado: " + str(error.code))
            print(error.info())
            error_message = error.read().decode("utf8", 'ignore')
            print(error_message)
            return jsonify({'response': 'Ocurrió un error: ' + error_message}), error.code
    else:
        return jsonify({'response': 'No se recibió ningún mensaje o número de expediente'}), 400

if __name__ == '__main__':
    app.run()

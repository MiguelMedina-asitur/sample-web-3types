import os
import ssl
import json
import urllib.request

import streamlit as st
from dotenv import load_dotenv

def allowSelfSignedHttps(allowed):
    # Ignore certificate verification on client side
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

allowSelfSignedHttps(True)  # Allow self-signed certificates

load_dotenv()  # Load environment variables from .env file

def main():
    st.title("Bienvenido")

    # Check if name is in session state
    if 'name' not in st.session_state:
        name = st.text_input("Por favor, ingresa tu nombre:")
        if name:
            st.session_state['name'] = name
            st.experimental_rerun()
        else:
            st.stop()
    else:
        st.write(f"Hola, {st.session_state['name']}!")

        # Display options
        options = ["Alertas proveedores", "Chat RIS", "indemnizables: seguimiento"]
        selected_option = st.selectbox("Por favor, selecciona una opción:", options)

        # Now, depending on the selected option, display different UIs
        if selected_option == "Alertas proveedores":
            # Implement the promptflow functionality
            promptflow_app()
        elif selected_option == "Chat RIS":
            # Implement the chat functionality
            chat_app()
        elif selected_option == "indemnizables: seguimiento":
            # Implement the seguimiento_chat functionality
            seguimiento_chat_app()

def promptflow_app():
    st.subheader("Alertas proveedores")

    # Create a form to collect inputs
    with st.form(key='promptflow_form'):
        periodo_actual = st.text_input("Periodo Archivo Actual", '')
        periodo_antiguo = st.text_input("Periodo Archivo Antiguo", '')
        ruta_antiguo = st.text_input("Ruta Archivo Antiguo", '')
        ruta_actual = st.text_input("Ruta Archivo Actual", '')

        submit_button = st.form_submit_button(label='Enviar')

    if submit_button:
        # Prepare the payload
        payload = {
            "periodoArchivoActual": periodo_actual,
            "periodoArchivoAntiguo": periodo_antiguo,
            "rutaArchivoAntiguo": ruta_antiguo,
            "rutaArchivoActual": ruta_actual
        }

        body = str.encode(json.dumps(payload))

        # Get the URL and API key from environment variables
        url = os.getenv('ENDPOINT_1')
        api_key = os.getenv('KEY_1')

        if not api_key:
            st.error('Falta la clave API')
            st.stop()

        headers = {'Content-Type': 'application/json', 'Authorization': ('Bearer ' + api_key)}

        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req)
            result = response.read()
            # Convert bytes to string
            result_str = result.decode('utf-8')
            # Load JSON
            result_json = json.loads(result_str)
            # Get the content of 'campo_output'
            campo_output = 'desarrollo'
            response_message = result_json.get(campo_output, 'No hay respuesta del API')
            st.success(response_message)
        except urllib.error.HTTPError as error:
            st.error(f"La solicitud falló con el código de estado: {error.code}")
            error_message = error.read().decode("utf8", 'ignore')
            st.error(f"Ocurrió un error: {error_message}")

def chat_app():
    st.subheader("Chat RIS")

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    # Display chat history
    for chat in st.session_state['chat_history']:
        st.write(f"**Usuario**: {chat['inputs']['question']}")
        if 'outputs' in chat:
            st.write(f"**Bot**: {chat['outputs']['answer']}")

    # Input for new message
    message = st.text_input("Tu mensaje:", key='chat_input')

    if st.button("Enviar", key='chat_send'):
        if message:
            # Add the message to chat history
            st.session_state['chat_history'].append({'inputs': {'question': message}})

            # Prepare the payload
            payload = {
                'question': message,
                'chat_history': [h for h in st.session_state['chat_history'][:-1] if 'outputs' in h]
            }

            body = str.encode(json.dumps(payload))

            # Get the URL and API key from environment variables
            url = os.getenv('ENDPOINT_2')
            api_key = os.getenv('KEY_2')

            if not api_key:
                st.error('Falta la clave API')
                st.stop()

            headers = {'Content-Type': 'application/json', 'Authorization': ('Bearer ' + api_key)}

            req = urllib.request.Request(url, body, headers)

            try:
                response = urllib.request.urlopen(req)
                result = response.read()
                result_json = json.loads(result.decode('utf-8'))
                respuesta = result_json.get('answer', 'No hay respuesta del API')

                # Add the response to chat history
                st.session_state['chat_history'][-1]['outputs'] = {'answer': respuesta}
                st.experimental_rerun()
            except urllib.error.HTTPError as error:
                st.error(f"La solicitud falló con el código de estado: {error.code}")
                error_message = error.read().decode("utf8", 'ignore')
                st.error(f"Ocurrió un error: {error_message}")
        else:
            st.error("No se recibió ningún mensaje")

def seguimiento_chat_app():
    st.subheader("Indemnizables: seguimiento")

    # Input for numero_expediente
    numero_expediente = st.text_input("Número de Expediente:", key='numero_expediente')

    if numero_expediente:
        # Check if 'seguimiento_chat_history' exists in session_state
        if 'seguimiento_chat_history' not in st.session_state:
            st.session_state['seguimiento_chat_history'] = {}

        # Option to reset chat history
        if st.button("Reiniciar Historial de Chat"):
            st.session_state['seguimiento_chat_history'][numero_expediente] = []

        expediente_history = st.session_state['seguimiento_chat_history'].get(numero_expediente, [])

        # Display chat history for this expediente
        for chat in expediente_history:
            st.write(f"**Usuario**: {chat['inputs']['question']}")
            if 'outputs' in chat:
                st.write(f"**Bot**: {chat['outputs']['answer']}")

        # Input for new message
        message = st.text_input("Tu mensaje:", key='seguimiento_chat_input')

        if st.button("Enviar", key='seguimiento_chat_send'):
            if message:
                # Add the message to expediente_history
                expediente_history.append({'inputs': {'question': message}})

                # Prepare the payload
                payload = {
                    'question': message,
                    'chat_history': [h for h in expediente_history[:-1] if 'outputs' in h],
                    'numero expediente': numero_expediente
                }

                body = str.encode(json.dumps(payload))

                # Get the URL and API key from environment variables
                url = os.getenv('ENDPOINT_3')
                api_key = os.getenv('KEY_3')

                if not api_key:
                    st.error('Falta la clave API')
                    st.stop()

                headers = {'Content-Type': 'application/json', 'Authorization': ('Bearer ' + api_key)}

                req = urllib.request.Request(url, body, headers)

                try:
                    response = urllib.request.urlopen(req)
                    result = response.read()
                    result_json = json.loads(result.decode('utf-8'))
                    respuesta = result_json.get('answer', 'No hay respuesta del API')

                    # Add the response to expediente_history
                    expediente_history[-1]['outputs'] = {'answer': respuesta}

                    # Update the history in session_state
                    st.session_state['seguimiento_chat_history'][numero_expediente] = expediente_history
                    st.experimental_rerun()
                except urllib.error.HTTPError as error:
                    st.error(f"La solicitud falló con el código de estado: {error.code}")
                    error_message = error.read().decode("utf8", 'ignore')
                    st.error(f"Ocurrió un error: {error_message}")
            else:
                st.error("No se recibió ningún mensaje")
    else:
        st.info("Por favor, ingresa el número de expediente")

if __name__ == '__main__':
    main()

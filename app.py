import os
from flask import Flask, request, render_template, jsonify, session, redirect, url_for
import requests
from bs4 import BeautifulSoup
from llama_index import SimpleDirectoryReader, VectorStoreIndex
from llama_index.query_engine import RetrieverQueryEngine
from wtforms import Form, StringField, validators
from tenacity import RetryError
from openai.error import AuthenticationError
import openai
from datetime import timedelta

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY')

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)


class UrlForm(Form):
    web_url = StringField('Web URL', [validators.URL(), validators.DataRequired()])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        if not api_key:
            return render_template('index.html', error='API Key is required')
        # Store the API key in session for subsequent requests
        session['api_key'] = api_key
        return redirect(url_for('use_api'))
    return render_template('index.html')


@app.route('/use_api', methods=['POST'])
def use_api():
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        if not api_key:
            return jsonify(success=False, error='API Key is required'), 400

        # Store the API key in session for subsequent requests
        session['api_key'] = api_key
        
        # Set the OpenAI API key environment variable
        # os.environ['OPENAI_API_KEY'] = api_key

        # Test the API key by making a request to OpenAI
        try:
            openai.api_key = api_key
            openai.Model.list()
        except Exception as e:
            return jsonify(success=False, error=str(e)), 400

        return jsonify(success=True, message='API Key submitted and tested successfully')
        
    # Handle GET requests or other methods here
    api_key = session.get('api_key')
    if not api_key:
        return redirect(url_for('index'))

    return 'Using API key: ' + api_key




@app.route('/fetch_text', methods=['POST'])
def fetch_text():
    web_url = request.form.get('web_url')
    if not web_url:
        return jsonify(success=False, error='Webpage URL is required'), 400
    try:
        response = requests.get(web_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()

        # Save text to a file
        with open('./data/webpage.txt', 'w', encoding='utf-8') as file:
            file.write(text)

        # Load documents
        documents = SimpleDirectoryReader('./data').load_data()
        
        # Construct Index
        index = VectorStoreIndex.from_documents(documents)

        # Query the index with a summary request
        query_engine = index.as_query_engine()
        summary_response = str(query_engine.query("Provide a concise summary of the key points in the text."))

        return jsonify(success=True, summary=summary_response)
    except requests.RequestException as e:
        return jsonify(success=False, error=str(e)), 500
    

@app.after_request
def add_security_headers(response):
    csp = ("default-src 'self'; "
           "img-src 'self' https://cdn.buymeacoffee.com; "
           "script-src 'self' 'unsafe-inline' https://cdnjs.buymeacoffee.com; ")
    response.headers['Content-Security-Policy'] = csp
    return response

if __name__ == '__main__':
    app.run(port=5000)

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
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import send_from_directory
from urllib.parse import unquote
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY')

if os.environ.get("FLASK_ENV") == "production":
    app.config.from_object("config.ProductionConfig")
else:
    app.config.from_object("config.DevelopmentConfig")

db = SQLAlchemy(app)

class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), unique=True, nullable=False)
    summary_text = db.Column(db.Text, nullable=False)





migrate = Migrate(app, db)

class UrlForm(Form):
    web_url = StringField('Web URL', [validators.URL(), validators.DataRequired()])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        web_url = request.form.get('web_url')  # Get the submitted URL
        api_key = request.form.get('api_key')

        if web_url:
            existing_summary = Summary.query.from_statement(text("SELECT * FROM Summary WHERE url = :url")).params(url=web_url).first()
            if existing_summary:
                return redirect(url_for('show_summary', url_from_route=web_url))  # Redirect if summary exists

        if api_key:
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


@app.route('/ads.txt')
def serve_ads_txt():
    return send_from_directory('static', 'ads.txt')



@app.route('/fetch_text', methods=['POST'])
def fetch_text():
    web_url = request.form.get('web_url')
    if not web_url:
        return jsonify(success=False, error='Webpage URL is required'), 400
    
    # Check if URL already exists in the database
    existing_summary = Summary.query.from_statement(text("SELECT * FROM Summary WHERE url = :url")).params(url=web_url).first()
    if existing_summary:
        return jsonify(success=True, summary=existing_summary.summary_text)
    
    try:
        response = requests.get(web_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()

        # Save text to a file
        with open('./data/webpage.txt', 'w', encoding='utf-8') as file:
            file.write(page_text)

        # Load documents
        documents = SimpleDirectoryReader('./data').load_data()
        
        # Construct Index
        index = VectorStoreIndex.from_documents(documents)

        # Query the index with a summary request
        query_engine = index.as_query_engine()
        summary_response = str(query_engine.query("Provide a concise summary of the key points in the text."))

        # Save to database
        new_summary = Summary(url=web_url, summary_text=summary_response)
        db.session.add(new_summary)
        db.session.commit()

        return jsonify(success=True, summary=summary_response)

    except requests.RequestException as e:
        return jsonify(success=False, error=str(e)), 500
    except IntegrityError:
        db.session.rollback()
        return jsonify(success=False, error='Unique constraint failed'), 500

    

def fetch_summary_from_db(url_from_route):
    # Query the Summary table to get the entry with the given url
    # summary_obj = Summary.query.filter(Summary.url.like(f"%{url_from_route}%")).first()
    summary_obj = Summary.query.from_statement(text("SELECT * FROM Summary WHERE url = :url")).params(url=url_from_route).first()



    # If the entry exists, return its content, else return None
    if summary_obj:
        return summary_obj.summary_text
    else:
        return None

@app.route('/summary/<path:url_from_route>')
def show_summary(url_from_route):
    summary_text = fetch_summary_from_db(url_from_route)
    if summary_text is not None:
        return render_template('summary_page.html', summary=summary_text, url=url_from_route)
    else:
        return "Summary not found"  # Handle this case as you see fit


@app.after_request
def add_security_headers(response):
    csp = ("default-src 'self'; "
           "img-src 'self' https://cdn.buymeacoffee.com; "
           "script-src 'self' 'unsafe-inline' https://cdnjs.buymeacoffee.com; ")
    response.headers['Content-Security-Policy'] = csp
    return response

if __name__ == '__main__':
    print("URL Map:", app.url_map)
    app.run(port=5000)

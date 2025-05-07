from flask import Flask, render_template, jsonify, request
import configparser
import requests
import logging
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import psycopg2


hostname = 'localhost'
database = 'Library_managment'
username = 'postgres'
password = '1234'
port_id = 5432


app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/Library_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure logging to DEBUG level for detailed logs
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Load the configuration from the config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

# Get the API key and URL from the configuration
try:
    GEMINI_API_KEY = config.get('API', 'GEMINI_API_KEY')
    GEMINI_API_URL = config.get('API', 'GEMINI_API_URL')
    logging.info("Gemini API configuration loaded successfully.")
except Exception as e:
    logging.error("Error reading config.ini: %s", e)
    GEMINI_API_KEY = None
    GEMINI_API_URL = None

# Route to serve the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to serve viewer.html
@app.route('/viewer.html')
def viewer():
    return render_template('viewer.html')

# API route to fetch description from Gemini API
@app.route('/api/description', methods=['GET'])
def get_book():
    conn = psycopg2.connect("dbname=your_existing_db user=username password=password")
    cur = conn.cursor()
    cur.execute("SELECT * FROM book")  # Use your actual table name
    books = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(books)

def get_description():
    entity_name = request.args.get('name')
    logging.debug(f"Received request for entity name: {entity_name}")  # Changed to DEBUG

    if not entity_name:
        logging.warning("Missing entity name in request.")
        return jsonify({'error': 'Missing entity name'}), 400

    if not GEMINI_API_URL or not GEMINI_API_KEY:
        logging.error("Gemini API configuration missing.")
        return jsonify({'error': 'Server configuration error'}), 500

    # Prepare the JSON payload with explicit instructions
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"Provide a detailed description of '{entity_name}'"
                            "If it is a book include information about the setting, characters, themes, key concepts, and its influence. "
                            "Do not include any concluding remarks or questions."
                            "Do not mention any Note at the end about not including concluding remarks or questions."
                        )
                    }
                ]
            }
        ]
    }

    # Construct the API URL with the API key as a query parameter
    api_url_with_key = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # Log the API URL and payload for debugging
    logging.debug(f"API URL: {api_url_with_key}")
    logging.debug(f"Payload: {payload}")

    try:
        # Make the POST request to the Gemini API
        response = requests.post(
            api_url_with_key,  # Include the API key in the URL
            headers=headers,
            json=payload,
            timeout=10  # seconds
        )
        logging.debug(f"Gemini API response status: {response.status_code}")  # Changed to DEBUG

        if response.status_code != 200:
            logging.error(f"Failed to fetch description from Gemini API. Status code: {response.status_code}")
            logging.error(f"Response content: {response.text}")
            return jsonify({
                'error': 'Failed to fetch description from Gemini API',
                'status_code': response.status_code,
                'response': response.text
            }), 500

        response_data = response.json()
        # Extract the description from the response
        description = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No description available.')
        logging.debug(f"Fetched description: {description}")  # Changed to DEBUG

        return jsonify({'description': description})

    except requests.exceptions.RequestException as e:
        logging.error(f"Exception during Gemini API request: {e}")
        return jsonify({'error': 'Failed to connect to Gemini API', 'message': str(e)}), 500
    except ValueError as e:
        logging.error(f"JSON decoding failed: {e}")
        return jsonify({'error': 'Invalid JSON response from Gemini API', 'message': str(e)}), 500
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        return jsonify({'error': 'An unexpected error occurred', 'message': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Optional: Insert initial data
        try:
            from sqlalchemy import text
            with open('schema.sql') as f:
                db.session.execute(text(f.read()))
            with open('data.sql') as f:
                db.session.execute(text(f.read()))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.warning(f"Could not initialize data: {e}")
    
    app.run(debug=True)
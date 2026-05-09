"""
Flask frontend server for CrewAI Financial Analysis Dashboard
Serves the interactive stock analysis UI
"""

import os
from flask import Flask, render_template, send_file
from flask_cors import CORS

app = Flask(__name__, 
    static_folder='.', 
    template_folder='.',
    static_url_path='/static'
)

# Enable CORS to allow API calls to backend
CORS(app)

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'Frontend is running ✅'}

if __name__ == '__main__':
    # Run on port 3000 (frontend)
    # Backend runs on port 8000
    port = int(os.environ.get('FRONTEND_PORT', 3000))
    app.run(
        host='127.0.0.1',
        port=port,
        debug=True,
        use_reloader=True
    )

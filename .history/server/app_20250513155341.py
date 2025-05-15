from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration MongoDB
app.config["MONGO_URI"] = os.getenv("DB_URI")
mongo = PyMongo(app)

# Route de test
@app.route('/')
def home():
    return jsonify({"message": "API en ligne et connectée à MongoDB ✅"})

# Route pour tester la connexion à la base
@app.route('/test-db')
def test_db():
    try:
        mongo.db.test.find_one()
        return jsonify({"status": "Connexion à MongoDB réussie ✅"})
    except Exception as e:
        return jsonify({"status": "Erreur de connexion", "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

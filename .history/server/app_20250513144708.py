
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Initialisation de Flask
app = Flask(__name__)

# Connexion à MongoDB via Flask-PyMongo
app.config["MONGO_URI"] = os.getenv("DB_URI")
mongo = PyMongo(app)

# Route pour tester la connexion
@app.route('/')
def index():
    return jsonify({"message": "Bienvenue sur l'API Flask avec MongoDB!"})

# Route pour ajouter un utilisateur
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    user = {
        "name": data['name'],
        "email": data['email']
    }
    mongo.db.users.insert_one(user)
    return jsonify({"message": "Utilisateur ajouté avec succès!"})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

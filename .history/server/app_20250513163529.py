from flask import Flask, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
import os
from dotenv import load_dotenv
load_dotenv()  # Charger les variables d'environnement depuis le fichier .env


app = Flask(__name__)
CORS(app)

app.config["MONGO_URI"] = os.environ.get("DB_URI", "mongodb://localhost:27017/mongo-db")
mongo = PyMongo(app)

@app.route("/")
def home():
    return jsonify({"message": "Bienvenue sur l'API Flask avec MongoDB!"})

@app.route("/test-db", methods=["GET"])
def test_db():
    try:
        mongo.db.test_collection.insert_one({"test": "ok"})
        return jsonify({"status": "Connexion à MongoDB réussie ✅"}), 200
    except Exception as e:
        return jsonify({"status": "Erreur de connexion à MongoDB ❌", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

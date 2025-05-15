from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Config PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Exemple de modèle
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test = db.Column(db.String(50), nullable=False)

@app.route("/")
def home():
    return jsonify({"message": "Bienvenue sur l'API Flask avec PostgreSQL!"})

@app.route("/test-db")
def test_db():
    try:
        # Crée la table si elle n'existe pas
        db.create_all()
        test = Test(test="ok")
        db.session.add(test)
        db.session.commit()
        return jsonify({"status": "Connexion à PostgreSQL réussie ✅"}), 200
    except Exception as e:
        return jsonify({"status": "Erreur de connexion à PostgreSQL ❌", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

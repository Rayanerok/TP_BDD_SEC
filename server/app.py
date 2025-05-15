from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta
import os
import jwt
from schemas import UserSchema
from marshmallow import ValidationError


# Charger les variables d'environnement
load_dotenv()

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "postgresql://postgres:password@localhost:5432/postgres")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SECRET_KEY = os.environ.get("SECRET_KEY", "mysecretkey")

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

# -------------------- MODELE --------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

# Créer les tables
with app.app_context():
    db.create_all()

# -------------------- SECURITE --------------------

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token manquant!'}), 403
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token invalide!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated_function

# -------------------- ROUTES PUBLIQUES --------------------

@app.route('/')
def home():
    return jsonify({"message": "Bienvenue sur l'API avec PostgreSQL 🚀"})

@app.route('/test-db', methods=["GET"])
def test_db():
    try:
        user = User(name="Rayane")
        db.session.add(user)
        db.session.commit()
        return jsonify({"status": "Connexion et insertion réussies ✅"}), 200
    except Exception as e:
        return jsonify({"status": "Erreur de connexion ❌", "error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(name=data['name']).first()
    if user:
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})
    return jsonify({'message': 'Utilisateur non trouvé'}), 401

# -------------------- CRUD UTILISATEUR --------------------

@app.route('/users', methods=["GET"])
@token_required
def get_users(current_user):
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.name} for u in users])



user_schema = UserSchema()



@app.route('/users', methods=["POST"])
def create_user():
    json_data = request.get_json()
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"error": "Le champ 'name' est requis"}), 400
    user = User(name=name)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Utilisateur créé", "id": user.id}), 201

@app.route('/users/<int:user_id>', methods=["PUT"])
@token_required
def update_user(current_user, user_id):
    data = request.get_json()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    user.name = data.get("name", user.name)
    db.session.commit()
    return jsonify({"message": "Utilisateur mis à jour"})

@app.route('/users/<int:user_id>', methods=["DELETE"])
@token_required
def delete_user(current_user, user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Utilisateur supprimé"})

# -------------------- EXECUTION --------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

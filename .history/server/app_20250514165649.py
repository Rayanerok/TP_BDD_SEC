from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta
import os
import jwt
import bcrypt

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
    password = db.Column(db.String(200), nullable=False)  # Ajout du champ password

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
        user = User(name="Rayane", password="hashedpassword")
        db.session.add(user)
        db.session.commit()
        return jsonify({"status": "Connexion et insertion réussies ✅"}), 200
    except Exception as e:
        return jsonify({"status": "Erreur de connexion ❌", "error": str(e)}), 500

# -------------------- LOGIN --------------------

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(name=data['name']).first()
    if user and bcrypt.checkpw(data['password'].encode('utf-8'), user.password):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})
    return jsonify({'message': 'Utilisateur non trouvé'}), 401

# -------------------- CRUD UTILISATEUR --------------------

@app.route('/users', methods=["POST"])
def create_user():
    data = request.get_json()
    
    # Validation simple
    if 'name' not in data or not data['name'] or not data['name'].isalnum():
        return jsonify({'error': "Le champ 'name' est requis et doit contenir uniquement des lettres et des chiffres."}), 400
    if 'password' not in data or not data['password']:
        return jsonify({'error': 'Le mot de passe est requis'}), 400

    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

    user = User(name=data['name'], password=hashed_password)
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
    
    # Mise à jour du nom si présent et valide
    if 'name' in data:
        name = data['name']
        if name and name.isalnum():
            user.name = name
        else:
            return jsonify({"error": "Le nom doit être alphanumérique."}), 400
    
    # Mise à jour du mot de passe si présent
    if 'password' in data:
        password = data['password']
        if password:
            user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        else:
            return jsonify({"error": "Le mot de passe ne peut pas être vide."}), 400

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
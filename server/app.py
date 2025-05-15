from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta
import os
import jwt
from schemas import UserSchema
from marshmallow import ValidationError
import bleach
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Charger les variables d'environnement
load_dotenv()

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)
 #Configuration du rate limiter pour limiter le nombre de requêtes par IP
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=[]
)
# Configuration de la base de données
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # Limite de 1 Mo
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "postgresql://postgres:password@localhost:5432/postgres")

SECRET_KEY = os.environ.get("SECRET_KEY", "mysecretkey")

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

# -------------------- MODELE --------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # unique=True pour éviter doublons
    password_hash = db.Column(db.String(512), nullable=False)



    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
        user.set_password("test123")
        db.session.add(user)
        db.session.commit()
        return jsonify({"status": "Connexion et insertion réussies ✅"}), 200
    except Exception as e:
        return jsonify({"status": "Erreur de connexion ❌", "error": str(e)}), 500

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Cette route ne peut être appelée que 5 fois par minute par IP
def login():
    try:
        data = request.get_json()
        print("DATA:", data)

        if not data or not data.get('name') or not data.get('password'):
            return jsonify({'message': "Nom d'utilisateur et mot de passe requis"}), 400

        user = User.query.filter_by(name=data['name']).first()
        print("USER:", user)

        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 401

        if not user.check_password(data['password']):
            return jsonify({'message': 'Mot de passe incorrect'}), 401

        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, SECRET_KEY, algorithm='HS256')

        return jsonify({'token': token})
    
    except Exception as e:
        print("ERREUR LOGIN:", str(e))  # <--- pour voir l'erreur dans la console
        return jsonify({'error': 'Une erreur est survenue.'}), 500


# -------------------- CRUD UTILISATEUR --------------------

@app.route('/users', methods=["GET"])
@token_required
def get_users(current_user):
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.name} for u in users])

user_schema = UserSchema()

@app.route('/users', methods=["POST"])
#@token_required 
def create_user():
    json_data = request.get_json()
    try:
        data = user_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    name = bleach.clean(data["name"])
    password = json_data.get("password")
    if not password:
        return jsonify({"error": "Le champ 'password' est requis"}), 400

    user = User(name=name)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Utilisateur créé", "id": user.id}), 201

@app.route('/users/<int:user_id>', methods=["PUT"])
@token_required
def update_user(current_user, user_id):
    json_data = getattr(request, 'sanitized_json', request.get_json())
    try:
        data = user_schema.load(json_data, partial=True)  # partial=True pour update partiel
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    if 'name' in data:
        user.name = bleach.clean(data['name'])

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

# ----------- Middleware global -----------

@app.before_request
def before_request_middleware():
    max_size = app.config.get('MAX_CONTENT_LENGTH')
    if max_size and request.content_length and request.content_length > max_size:
        abort(413, description="Payload trop volumineux")
    
    if request.is_json:
        json_data = request.get_json()
        
        def sanitize(data):
            if isinstance(data, dict):
                return {k: sanitize(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [sanitize(item) for item in data]
            elif isinstance(data, str):
                return bleach.clean(data)
            else:
                return data

        sanitized_data = sanitize(json_data)
        # Stockage temporaire dans request pour utiliser dans les routes
        request.sanitized_json = sanitized_data

# ----------- Gestion des erreurs globales -----------


@app.errorhandler(Exception)
def handle_generic_error(error):
    # Affiche l'erreur complète en debug pour comprendre ce qui se passe
    return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';

function Login({ onLogin }) {
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  const handleLogin = async (e) => {
    e.preventDefault();
    setMessage('');

    try {
      const response = await fetch('http://localhost:5000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, password }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('Connexion réussie ✅');
        localStorage.setItem('token', data.token); // Sauvegarde du token
        onLogin(data.token); // ✅ Appel du prop reçu
        navigate('/dashboard');
      } else {
        setMessage(data.message || 'Erreur lors de la connexion ❌');
      }
    } catch (error) {
      console.error(error);
      setMessage('Erreur réseau ❌');
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: 'auto', padding: 20 }}>
      <h2>Connexion</h2>
      <form onSubmit={handleLogin}>
        <input
          type="text"
          placeholder="Nom d'utilisateur"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          style={{ width: '100%', marginBottom: 10 }}
        />
        <input
          type="password"
          placeholder="Mot de passe"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ width: '100%', marginBottom: 10 }}
        />
        <button type="submit" style={{ width: '100%' }}>Se connecter</button>
      </form>
      <p>
      Pas encore inscrit ? <a href="/register">Créer un compte</a>
      </p>
      {message && <p>{message}</p>}
    </div>
  );
}

export default Login;

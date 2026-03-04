import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import './Login.css';

export default function Login() {
    const [username, setUsername] = useState('admin');
    const [password, setPassword] = useState('admin123');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const { data } = await api.post('/auth/login', {
                username,
                password,
                device_info: { hostname: "Web Portal", os_info: navigator.userAgent }
            });

            localStorage.setItem('admin_token', data.access_token);
            localStorage.setItem('admin_name', data.user.name);
            localStorage.setItem('is_admin', data.user.is_admin);

            // Cache these to simulate the punch in/out later
            localStorage.setItem('username_cache', username);
            localStorage.setItem('password_cache', password);

            if (data.user.is_admin) {
                navigate('/admin-dashboard');
            } else {
                navigate('/employee-dashboard');
            }

        } catch (err) {
            console.error("Login component error:", err);
            setError(err.response?.data?.detail || err.message || 'Invalid username or password.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="glass-panel login-card">
                <h2 className="title">Admin Portal</h2>
                <p className="subtitle">Sahastra Finnovations Pvt. Ltd.</p>

                {error && <div className="error-alert">{error}</div>}

                <form onSubmit={handleLogin}>
                    <div className="input-group">
                        <input
                            type="text"
                            placeholder="Admin ID"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            disabled={loading}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <input
                            type="password"
                            placeholder="Secure Password"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            disabled={loading}
                            required
                        />
                    </div>
                    <button type="submit" className="login-btn" disabled={loading}>
                        {loading ? 'Authenticating...' : 'Sign In To Dashboard'}
                    </button>
                </form>
            </div>
        </div>
    );
}

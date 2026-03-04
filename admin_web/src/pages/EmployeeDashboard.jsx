import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, PieChart, Calendar, Clock } from 'lucide-react';
import api from '../api';
import './EmployeeDashboard.css';

// Re-using the Pie Chart logic visually, adapted for React Canvas/SVG
function StatPieChart({ stats }) {
    const total = stats.present + stats.absent + stats.approved_leaves;
    if (total === 0) return <div className="no-data">No Data Available Yet For This Month</div>;

    const getAngle = (value) => (value / total) * 360;

    let currentAngle = 0;

    // SVG Pie Chart rendering
    const createSlice = (value, color) => {
        if (value === 0) return null;
        const angle = getAngle(value);

        // Convert polar to cartesian
        const startX = 100 + 80 * Math.cos(Math.PI * currentAngle / 180);
        const startY = 100 + 80 * Math.sin(Math.PI * currentAngle / 180);
        const endX = 100 + 80 * Math.cos(Math.PI * (currentAngle + angle) / 180);
        const endY = 100 + 80 * Math.sin(Math.PI * (currentAngle + angle) / 180);

        // Large arc flag
        const largeArc = angle > 180 ? 1 : 0;

        const pathData = `M 100 100 L ${startX} ${startY} A 80 80 0 ${largeArc} 1 ${endX} ${endY} Z`;

        currentAngle += angle;
        return <path key={color} d={pathData} fill={color} />;
    };

    // Reset angle for rendering
    currentAngle = 0;

    return (
        <div className="chart-container">
            <svg width="200" height="200" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="80" fill="#f0f3f4" />
                {createSlice(stats.present, '#2ECC71')}
                {createSlice(stats.absent, '#E74C3C')}
                {createSlice(stats.approved_leaves, '#F1C40F')}
            </svg>
            <div className="chart-legend">
                <div className="legend-item"><span className="dot present"></span> Present: {stats.present}</div>
                <div className="legend-item"><span className="dot absent"></span> Absent: {stats.absent}</div>
                <div className="legend-item"><span className="dot leave"></span> Approved Leaf: {stats.approved_leaves}</div>
            </div>
        </div>
    );
}

export default function EmployeeDashboard() {
    const [activeTab, setActiveTab] = useState('Overview');
    const [stats, setStats] = useState({ present: 0, absent: 0, approved_leaves: 0 });
    const [myLeaves, setMyLeaves] = useState([]);

    // Leave Form
    const [leaveType, setLeaveType] = useState('LONG');
    const [reason, setReason] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [loading, setLoading] = useState(false);
    const [activeSession, setActiveSession] = useState(false); // Are we checked-in?

    const navigate = useNavigate();
    const employeeName = localStorage.getItem('admin_name') || 'Employee';

    const fetchData = async () => {
        setLoading(true);
        try {
            const [stResp, lvResp] = await Promise.all([
                api.get('/attendance/stats'),
                api.get('/leaves')
            ]);
            setStats({
                present: stResp.data.present || 0,
                absent: stResp.data.absent || 0,
                approved_leaves: stResp.data.approved_leaves || 0
            });
            setMyLeaves(lvResp.data.leaves);
        } catch (err) {
            if (err.response?.status === 401) {
                handleLogout();
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // In a real app we would check active session status from backend here.
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_name');
        navigate('/login');
    };

    const submitLeave = async (e) => {
        e.preventDefault();
        try {
            await api.post('/leaves/apply', {
                leave_type: leaveType,
                reason,
                start_date: new Date(startDate).toISOString(),
                end_date: new Date(endDate).toISOString()
            });
            alert('Leave requested successfully.');
            setReason('');
            fetchData();
        } catch (err) {
            alert('Failed to submit leave.');
        }
    };

    const handleAttendance = async (action) => {
        try {
            if (action === 'in') {
                const device_info = { hostname: "Web Portal", os_info: navigator.userAgent };
                // We simulate a login hit to record attendance
                await api.post('/auth/login', {
                    username: localStorage.getItem('username_cache'), // We need to store this on login
                    password: localStorage.getItem('password_cache'),
                    device_info
                });
                setActiveSession(true);
                alert('Checked in successfully!');
            } else {
                await api.post('/auth/logout');
                setActiveSession(false);
                alert('Checked out. Session recorded.');
                fetchData(); // refresh stats
            }
        } catch (err) {
            alert('Action failed. Note: you might need to re-login.');
        }
    };

    return (
        <div className="emp-layout">
            {/* Sidebar */}
            <aside className="glass-panel emp-sidebar">
                <div className="brand">
                    <h2>Sahastra<br />Finnovations</h2>
                    <p>Employee Portal</p>
                </div>
                <nav className="nav-menu">
                    <button className={`nav-item ${activeTab === 'Overview' ? 'active' : ''}`} onClick={() => setActiveTab('Overview')}><PieChart size={18} /> My Overview</button>
                    <button className={`nav-item ${activeTab === 'Leaves' ? 'active' : ''}`} onClick={() => setActiveTab('Leaves')}><Calendar size={18} /> My Leaves</button>
                </nav>
                <div className="emp-sidebar-footer">
                    <button className="logout-btn" onClick={handleLogout}><LogOut size={18} /> Logout</button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="emp-main">
                <header className="glass-panel emp-header">
                    <div className="header-title">
                        <h1>{activeTab === 'Overview' ? 'Dashboard Overview' : 'Leave Management'}</h1>
                        <p className="welcome-text">Welcome back, {employeeName}</p>
                    </div>
                    <div className="header-actions">
                        {!activeSession ? (
                            <button className="btn-success check-btn" onClick={() => handleAttendance('in')}><Clock size={16} /> Punch In To Work</button>
                        ) : (
                            <button className="btn-danger check-btn" onClick={() => handleAttendance('out')}><Clock size={16} /> Punch Out</button>
                        )}
                        <button className="refresh-btn" onClick={fetchData} disabled={loading}>{loading ? 'Syncing...' : 'Refresh'}</button>
                    </div>
                </header>

                <div className="emp-content-grid">
                    {activeTab === 'Overview' && (
                        <div className="glass-panel emp-card">
                            <h2>Monthly Attendance Breakdown</h2>
                            <StatPieChart stats={stats} />
                        </div>
                    )}

                    {activeTab === 'Leaves' && (
                        <>
                            <div className="glass-panel emp-card">
                                <h2>Apply For Leave</h2>
                                <form onSubmit={submitLeave} className="leave-form">
                                    <div className="form-row">
                                        <select value={leaveType} onChange={e => setLeaveType(e.target.value)}>
                                            <option value="LONG">Long Leave</option>
                                            <option value="PRIOR">Prior Info Leave</option>
                                            <option value="EMERGENCY">Emergency Leave</option>
                                        </select>
                                    </div>
                                    <div className="form-row dates">
                                        <div>
                                            <label>Start Date</label>
                                            <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required />
                                        </div>
                                        <div>
                                            <label>End Date</label>
                                            <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} required />
                                        </div>
                                    </div>
                                    <div className="form-row">
                                        <textarea placeholder="Reason for leave..." value={reason} onChange={e => setReason(e.target.value)} required rows="3"></textarea>
                                    </div>
                                    <button type="submit" className="login-btn submit-leave">Submit Request</button>
                                </form>
                            </div>

                            <div className="glass-panel emp-card no-flex">
                                <h2>My Leave History</h2>
                                <div className="table-responsive">
                                    <table>
                                        <thead>
                                            <tr><th>Type</th><th>Start Date</th><th>End Date</th><th>Reason</th><th>Status</th></tr>
                                        </thead>
                                        <tbody>
                                            {myLeaves.map((lv, i) => (
                                                <tr key={i}>
                                                    <td>{lv.type}</td>
                                                    <td>{lv.start_date.split('T')[0]}</td>
                                                    <td>{lv.end_date.split('T')[0]}</td>
                                                    <td>{lv.reason}</td>
                                                    <td className={`status-${lv.status.toLowerCase()}`}>{lv.status}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}

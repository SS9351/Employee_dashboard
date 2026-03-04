import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Users, Clock, FileText, KeyRound, Download, Trash2 } from 'lucide-react';
import api, { adminApi } from '../api';
import './Dashboard.css';

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState('Leaves');
    const [users, setUsers] = useState([]);
    const [empFilter, setEmpFilter] = useState('All Employees');

    // Data States
    const [leaves, setLeaves] = useState([]);
    const [attendance, setAttendance] = useState([]);
    const [actualAttendance, setActualAttendance] = useState([]);
    const [logs, setLogs] = useState([]);
    const [resets, setResets] = useState([]);
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();
    const adminName = localStorage.getItem('admin_name') || 'Administrator';

    const fetchData = async () => {
        setLoading(true);
        try {
            // Parallel requests for speed
            const [usr, lvs, att, act, lg, rst] = await Promise.all([
                api.get('/admin/users'),
                api.get('/admin/leaves'),
                api.get('/admin/attendance'),
                api.get('/admin/actual-attendance'),
                api.get('/admin/logs'),
                api.get('/admin/reset-requests')
            ]);
            setUsers(usr.data.users);
            setLeaves(lvs.data.leaves);
            setAttendance(att.data.attendance);
            setActualAttendance(act.data.actual_attendance);
            setLogs(lg.data.logs);
            setResets(rst.data.requests);
        } catch (err) {
            if (err.response?.status === 401 || err.response?.status === 403) {
                handleLogout();
            }
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_name');
        localStorage.removeItem('is_admin');
        localStorage.removeItem('username_cache');
        localStorage.removeItem('password_cache');
        navigate('/login');
    };

    const handleLeaveAction = async (id, status) => {
        try {
            await api.post(`/admin/leaves/${id}/status`, { status });
            fetchData();
        } catch (err) { alert('Failed to update leave.'); }
    };

    const handleApproveReset = async (id) => {
        try {
            await api.post(`/admin/reset-requests/${id}/approve`);
            fetchData();
        } catch (err) { alert('Failed to approve request.'); }
    };

    const handleTerminateSession = async (id) => {
        if (!window.confirm("Are you sure you want to forcibly terminate this user's active session?")) return;
        try {
            await adminApi.terminateSession(id);
            fetchData();
        } catch (err) { alert(err.response?.data?.detail || 'Failed to terminate session.'); }
    };

    const handleToggleAdminStatus = async (userId) => {
        if (!window.confirm("Are you sure you want to toggle this user's admin privilege?")) return;
        try {
            await adminApi.toggleAdmin(userId);
            fetchData();
        } catch (err) { alert(err.response?.data?.detail || 'Failed to toggle admin status.'); }
    };

    const handleExportExcel = async () => {
        try {
            const response = await adminApi.exportToExcel();
            // Create a blob link to trigger a native download
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `sahastra_export_${new Date().getTime()}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
        } catch (err) { alert('Failed to export to Excel.'); }
    };

    const handleDeleteLogs = async () => {
        if (!window.confirm("WARNING: This will permanently delete ALL application logs! You MUST have exported them to Excel in the last 2 minutes. Proceed?")) return;
        try {
            const res = await adminApi.deleteLogs();
            alert(res.data.message);
            fetchData();
        } catch (err) { alert(err.response?.data?.detail || 'Failed to delete logs. Did you forget to Export first?'); }
    };

    // Helper Filter Method
    const filterData = (dataList, key) => {
        if (empFilter === 'All Employees') return dataList;
        return dataList.filter(d => d[key] === empFilter);
    };

    const tabs = [
        { id: 'Users', label: 'All Employees', icon: <Users size={18} /> },
        { id: 'Leaves', label: 'Leave Management', icon: <FileText size={18} /> },
        { id: 'Actual', label: 'Actual Attendance', icon: <Clock size={18} /> },
        { id: 'Attendance', label: 'Live Sessions', icon: <Users size={18} /> },
        { id: 'Logs', label: 'Application Logs', icon: <FileText size={18} /> },
        { id: 'Resets', label: 'Password Resets', icon: <KeyRound size={18} /> },
    ];

    return (
        <div className="dashboard-layout">
            {/* Sidebar */}
            <aside className="glass-panel sidebar">
                <div className="brand">
                    <h2>Sahastra<br />Finnovations</h2>
                    <p>Admin Portal</p>
                </div>
                <nav className="nav-menu">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            {tab.icon} {tab.label}
                        </button>
                    ))}
                </nav>
                <div className="sidebar-footer">
                    <button className="logout-btn" onClick={handleLogout}>
                        <LogOut size={18} /> Logout
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                <header className="glass-panel top-header">
                    <div className="header-title">
                        <h1>{tabs.find(t => t.id === activeTab)?.label}</h1>
                        <p className="welcome-text">Welcome back, {adminName}</p>
                    </div>
                    <div className="header-actions">
                        <select
                            className="emp-filter"
                            value={empFilter}
                            onChange={e => setEmpFilter(e.target.value)}
                        >
                            <option>All Employees</option>
                            {users.map(u => <option key={u.id}>{u.full_name || u.username}</option>)}
                        </select>
                        <button className="refresh-btn" style={{ backgroundColor: '#10b981' }} onClick={handleExportExcel}>
                            <Download size={16} /> Export
                        </button>
                        <button className="refresh-btn" style={{ backgroundColor: '#ef4444' }} onClick={handleDeleteLogs}>
                            <Trash2 size={16} /> Delete Logs
                        </button>
                        <button className="refresh-btn" onClick={fetchData} disabled={loading}>
                            {loading ? 'Syncing...' : 'Refresh Data'}
                        </button>
                    </div>
                </header>

                <div className="glass-panel data-container">
                    <div className="table-responsive">
                        <table>
                            {activeTab === 'Leaves' && (
                                <>
                                    <thead>
                                        <tr>
                                            <th>Employee</th><th>Type</th><th>Reason</th><th>Status</th><th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filterData(leaves, 'employee_name').map((lv, i) => (
                                            <tr key={i}>
                                                <td>{lv.employee_name}</td>
                                                <td>{lv.type}</td>
                                                <td>{lv.reason}</td>
                                                <td className={`status-${lv.status.toLowerCase()}`}>{lv.status}</td>
                                                <td>
                                                    {lv.status === 'PENDING' ? (
                                                        <div className="action-buttons">
                                                            <button className="btn-success" onClick={() => handleLeaveAction(lv.id, 'APPROVED')}>Approve</button>
                                                            <button className="btn-danger" onClick={() => handleLeaveAction(lv.id, 'REJECTED')}>Reject</button>
                                                        </div>
                                                    ) : '-'}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </>
                            )}

                            {activeTab === 'Actual' && (
                                <>
                                    <thead>
                                        <tr>
                                            <th>Date</th><th>Employee</th><th>Login</th><th>Logout</th><th>Hrs Work</th><th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filterData(actualAttendance, 'employee_name').map((act, i) => (
                                            <tr key={i}>
                                                <td>{act.date}</td>
                                                <td>{act.employee_name}</td>
                                                <td>{act.login_time}</td>
                                                <td>{act.logout_time}</td>
                                                <td>{act.duration}</td>
                                                <td className={act.status.includes('Present') ? 'status-approved' : 'status-rejected'}>
                                                    {act.status}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </>
                            )}

                            {activeTab === 'Attendance' && (
                                <>
                                    <thead>
                                        <tr>
                                            <th>Employee</th><th>Login Time</th><th>Logout Time</th><th>IP Address</th><th>MAC Address</th><th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filterData(attendance, 'employee_name').map((at, i) => (
                                            <tr key={i}>
                                                <td>{at.employee_name}</td>
                                                <td>{at.login_time}</td>
                                                <td>{at.logout_time || 'Active Session'}</td>
                                                <td>{at.ip}</td>
                                                <td>{at.mac_address}</td>
                                                <td>
                                                    {!at.logout_time ? (
                                                        <button className="btn-danger" onClick={() => handleTerminateSession(at.id)}>Terminate</button>
                                                    ) : '-'}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </>
                            )}

                            {activeTab === 'Logs' && (
                                <>
                                    <thead>
                                        <tr>
                                            <th>Employee</th><th>Time</th><th>Application</th><th>Window Title</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filterData(logs, 'employee_name').map((lg, i) => (
                                            <tr key={i}>
                                                <td>{lg.employee_name}</td>
                                                <td>{lg.time}</td>
                                                <td>{lg.app_name}</td>
                                                <td>{lg.raw_title}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </>
                            )}

                            {activeTab === 'Resets' && (
                                <>
                                    <thead>
                                        <tr>
                                            <th>ID</th><th>Employee</th><th>Username</th><th>Status</th><th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filterData(resets, 'employee_name').map((rs, i) => (
                                            <tr key={i}>
                                                <td>{rs.id}</td>
                                                <td>{rs.employee_name}</td>
                                                <td>{rs.username}</td>
                                                <td className={`status-${rs.status.toLowerCase()}`}>{rs.status}</td>
                                                <td>
                                                    {rs.status === 'PENDING' ? (
                                                        <button className="btn-success" onClick={() => handleApproveReset(rs.id)}>Approve Reset</button>
                                                    ) : '-'}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </>
                            )}

                            {activeTab === 'Users' && (
                                <>
                                    <thead>
                                        <tr>
                                            <th>ID</th><th>Full Name</th><th>Username</th><th>Status</th><th>Admin Privilege</th><th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {users.map((u, i) => (
                                            <tr key={i}>
                                                <td>{u.id}</td>
                                                <td>{u.full_name || '-'}</td>
                                                <td>{u.username}</td>
                                                <td>{u.is_active ? 'Active' : 'Inactive'}</td>
                                                <td style={{ fontWeight: 'bold', color: u.is_admin ? '#10b981' : '#64748b' }}>
                                                    {u.is_admin ? 'Administrator' : 'Standard'}
                                                </td>
                                                <td>
                                                    <button
                                                        className={u.is_admin ? "btn-danger" : "btn-success"}
                                                        onClick={() => handleToggleAdminStatus(u.id)}
                                                    >
                                                        {u.is_admin ? 'Revoke Admin' : 'Make Admin'}
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </>
                            )}
                        </table>
                    </div>
                </div>
            </main>
        </div>
    );
}

import axios from 'axios';

// When deployed to cloud, change this to the production URL.
const API_URL = 'https://employee-dashboard-iler.onrender.com/api';

const api = axios.create({
    baseURL: API_URL,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('admin_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const adminApi = {
    toggleAdmin: (userId) => api.post(`/admin/users/${userId}/toggle-admin`),
    terminateSession: (attendanceId) => api.post(`/admin/attendance/${attendanceId}/terminate`),
    exportToExcel: () => api.get('/admin/export-excel', { responseType: 'blob' }),
    deleteLogs: () => api.delete('/admin/logs')
};

export default api;

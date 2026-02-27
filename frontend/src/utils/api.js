// API utility for making authenticated requests
const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getStoredToken = () => localStorage.getItem('odapto_session_token');

export const apiCall = async (endpoint, options = {}) => {
  const token = getStoredToken();
  const headers = {
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }
  
  const response = await fetch(`${API}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include'
  });
  
  return response;
};

export const apiGet = (endpoint) => apiCall(endpoint, { method: 'GET' });
export const apiPost = (endpoint, body) => apiCall(endpoint, { method: 'POST', body });
export const apiPatch = (endpoint, body) => apiCall(endpoint, { method: 'PATCH', body });
export const apiDelete = (endpoint) => apiCall(endpoint, { method: 'DELETE' });

export default { apiCall, apiGet, apiPost, apiPatch, apiDelete };

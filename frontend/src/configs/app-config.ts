const hostname = window.location.hostname;
const isDev = hostname === 'localhost';

const devApiBaseUrl = 'http://localhost:8000/api/distiller';
const prodApiBaseUrl = '/api/distiller';
const apiBaseUrl = isDev ? devApiBaseUrl : prodApiBaseUrl;

export default {
  apiBaseUrl
};

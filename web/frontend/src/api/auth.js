import api from './index'

export const register = (username, password) => {
  return api.post('/auth/register', { username, password })
}

export const login = (username, password) => {
  return api.post('/auth/login', { username, password })
}

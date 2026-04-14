import { defineStore } from 'pinia'
import { login as apiLogin } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    username: localStorage.getItem('username') || null,
  }),
  
  actions: {
    async login(username, password) {
      const response = await apiLogin(username, password)
      this.token = response.data.access_token
      this.username = response.data.username
      
      localStorage.setItem('token', this.token)
      localStorage.setItem('username', this.username)
    },
    
    logout() {
      this.token = null
      this.username = null
      localStorage.removeItem('token')
      localStorage.removeItem('username')
    }
  }
})

import { defineStore } from 'pinia'
import { getPlatforms, shopLogin as apiShopLogin } from '../api/platforms'
import { getConfig, updateConfig as apiUpdateConfig } from '../api/config'

export const usePlatformStore = defineStore('platform', {
  state: () => ({
    platforms: [],
    currentPlatform: null,
    loginStatus: {
      loggedIn: false,
      shopName: '',
    },
    config: {
      shop_username: '',
      product_urls: [],
      has_login: false,
    }
  }),
  
  actions: {
    async loadPlatforms() {
      const response = await getPlatforms()
      this.platforms = response.data.platforms
    },
    
    async loadConfig(platformCode) {
      const response = await getConfig(platformCode)
      this.config = response.data
    },
    
    async updateConfig(platformCode, data) {
      await apiUpdateConfig(platformCode, data)
      await this.loadConfig(platformCode)
    },
    
    async shopLogin(platformCode, username, password, verifyCode = '', csrfToken = '') {
      const response = await apiShopLogin(platformCode, username, password, verifyCode, csrfToken)
      this.loginStatus = {
        loggedIn: response.data.success,
        shopName: response.data.shop_name || '',
      }
      return response.data
    }
  }
})

import { defineStore } from 'pinia'
import { 
  getPrice as apiGetPrice, 
  submitOrder as apiSubmitOrder,
  modifyPrice as apiModifyPrice,
  getOrders as apiGetOrders
} from '../api/platforms'

export const useOrderStore = defineStore('order', {
  state: () => ({
    processing: false,
    logs: [],
    qrCode: null,
    paymentUrl: null,
    priceInfo: null,
    // 订单查询相关
    orderList: [],
    orderQueryLoading: false,
    orderQueryParams: {},
  }),
  
  actions: {
    async getPrice(platformCode, productUrl) {
      const response = await apiGetPrice(platformCode, productUrl)
      this.priceInfo = response.data
      return response.data
    },
    
    async modifyPrice(platformCode, goodsId, newPrice) {
      const response = await apiModifyPrice(platformCode, goodsId, newPrice)
      return response.data
    },
    
    async processOrder(platformCode, productUrl, newPrice) {
      this.processing = true
      this.logs = []
      this.qrCode = null
      this.paymentUrl = null
      
      try {
        const response = await apiSubmitOrder(platformCode, productUrl, newPrice)
        this.logs = response.data.logs || []
        
        if (response.data.success) {
          this.qrCode = response.data.qr_code_base64
          this.paymentUrl = response.data.payment_url
        }
        
        return response.data
      } finally {
        this.processing = false
      }
    },
    
    async fetchOrders(platformCode, params) {
      this.orderQueryLoading = true
      this.orderQueryParams = params
      
      try {
        const response = await apiGetOrders(platformCode, params)
        this.orderList = response.data.orders || []
        return response.data
      } finally {
        this.orderQueryLoading = false
      }
    }
  }
})

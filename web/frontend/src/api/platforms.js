import api from './index'

export const getPlatforms = () => {
  return api.get('/platforms')
}

export const shopLogin = (platformCode, username, password) => {
  return api.post(`/platforms/${platformCode}/login`, {
    username,
    password,
  })
}

export const getPrice = (platformCode, productUrl) => {
  return api.post(`/platforms/${platformCode}/price`, {
    product_url: productUrl,
  })
}

export const submitOrder = (platformCode, productUrl, newPrice) => {
  return api.post(`/platforms/${platformCode}/order`, {
    product_url: productUrl,
    new_price: newPrice,
  })
}

export const modifyPrice = (platformCode, goodsId, newPrice) => {
  return api.post(`/platforms/${platformCode}/modify-price`, {
    goods_id: goodsId,
    new_price: newPrice,
  })
}

export const getOrders = (platformCode, params) => {
  return api.get(`/platforms/${platformCode}/orders`, { params })
}

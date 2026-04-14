import api from './index'

export const getConfig = (platformCode) => {
  return api.get(`/config/${platformCode}`)
}

export const updateConfig = (platformCode, data) => {
  return api.put(`/config/${platformCode}`, data)
}

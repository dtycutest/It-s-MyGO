import { defineStore } from 'pinia';
import { ref } from 'vue';
import { priceAlertApi } from '../api';
import type { PriceAlert } from '../api/types';

export const usePriceAlertStore = defineStore('priceAlert', () => {
  const alerts = ref<PriceAlert[]>([]);
  const loading = ref(false);

  const fetchAlerts = async (page = 1, pageSize = 20) => {
    loading.value = true;
    try {
      const res = await priceAlertApi.list(page, pageSize);
      alerts.value = res.data.list;
      return res;
    } finally {
      loading.value = false;
    }
  };

  const createAlert = async (productId: string, targetPrice: number) => {
    const res = await priceAlertApi.create({ product_id: productId, target_price: targetPrice });
    alerts.value.unshift(res.data);
    return res;
  };

  const deleteAlert = async (alertId: number) => {
    await priceAlertApi.delete(alertId);
    alerts.value = alerts.value.filter(a => a.alert_id !== alertId);
  };

  return { alerts, loading, fetchAlerts, createAlert, deleteAlert };
});
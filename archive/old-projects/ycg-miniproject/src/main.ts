import { createSSRApp } from 'vue';
import App from './App.vue';

console.log('[main.ts] 开始');

export function createApp() {
  console.log('[main.ts] createApp 调用');
  const app = createSSRApp(App);
  console.log('[main.ts] app 已创建');
  return { app };
}

console.log('[main.ts] 完成');

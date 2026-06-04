<script setup lang="ts">
console.log('[index.vue] setup 被调用');
</script>

<template>
  <view style="background: #fff8e1; padding: 30px; min-height: 100vh;">
    <view style="background: #ff9800; color: white; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
      🏠 首页正常工作！
    </view>
    
    <view style="font-size: 18px; color: #333;">
      index.vue 正常渲染
    </view>
    
    <view style="margin-top: 20px; padding: 20px; border: 2px dashed #ff9800; border-radius: 8px;">
      测试内容
    </view>
  </view>
</template>

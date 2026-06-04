<script setup lang="ts">
console.log('[App.vue] setup 被调用');
</script>

<template>
  <view style="background: #fff; padding: 30px; min-height: 100vh;">
    <view style="background: #28a745; color: white; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
      ✅ App.vue 正常工作！
    </view>
    
    <view style="font-size: 20px; color: #333; margin-bottom: 20px;">
      如果你能看到这个，说明 uni-app 已正确挂载！
    </view>
    
    <view style="border: 2px solid #007bff; padding: 20px; border-radius: 8px;">
      <text>测试内容 A</text>
    </view>
  </view>
</template>

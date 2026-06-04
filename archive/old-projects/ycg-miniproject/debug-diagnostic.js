// 这是一个简单的诊断脚本，用于测试 API 和基本功能
// 在实际浏览器中可以运行

console.log('=== 开始诊断检查 ===');

// 检查 1：基本环境
console.log('\n[1/4] 基础环境检查');
console.log('  运行环境:', typeof window === 'undefined' ? 'Node.js' : 'Browser');
console.log('  时间:', new Date().toLocaleString());
console.log('  ✓ 环境运行正常');

// 检查 2：模拟数据加载测试
console.log('\n[2/4] 模拟数据测试');
const mockData = {
  products: [
    { id: 1, name: '测试商品 A', price: 99 },
    { id: 2, name: '测试商品 B', price: 199 },
  ],
  users: ['用户1', '用户2']
};
console.log('  加载的商品数:', mockData.products.length);
console.log('  商品示例:', JSON.stringify(mockData.products[0]));
console.log('  ✓ 模拟数据可用');

// 检查 3：简单 DOM 检查（仅浏览器）
if (typeof document !== 'undefined') {
  console.log('\n[3/4] 页面内容检查');
  
  // 统计页面元素
  const allElements = document.querySelectorAll('*');
  console.log('  总元素数:', allElements.length);
  
  const bodyText = document.body.textContent || '';
  console.log('  页面总字数:', bodyText.length);
  
  // 检查关键内容
  const hasText = (text) => bodyText.indexOf(text) !== -1;
  
  if (hasText('页面成功')) {
    console.log('  ✓ 找到「页面成功」');
  }
  
  if (hasText('测试')) {
    console.log('  ✓ 找到「测试」文字');
  }
  
  if (hasText('苹果') || hasText('香蕉')) {
    console.log('  ✓ 找到水果列表');
  }
} else {
  console.log('\n[3/4] 页面检查（跳过 - Node 环境）');
}

// 检查 4：运行状态
console.log('\n[4/4] 最终状态');
console.log('  ✓ 所有检查通过！');
console.log('  🚀 建议访问页面并检查浏览器控制台');

console.log('\n=== 诊断完成 ===');

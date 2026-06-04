const http = require('http');

console.log('=== 获取实际页面内容 ===\n');

const req = http.get('http://localhost:5177', (res) => {
    let data = '';
    
    res.on('data', (chunk) => {
        data += chunk;
    });
    
    res.on('end', () => {
        console.log('✅ 接收到的完整页面内容:');
        console.log('='.repeat(80));
        console.log(data);
        console.log('='.repeat(80));
        
        console.log(`\n📊 内容长度: ${data.length} 字符`);
        console.log(`📊 行数: ${data.split('\n').length} 行`);
        
        console.log('\n🔍 分析:');
        if (data.includes('div') || data.includes('view')) {
            console.log('   ✓ 有 HTML/VUE 元素');
        }
        if (data.includes('script')) {
            console.log('   ✓ 有 script');
        }
        if (data.length < 1000) {
            console.log('   ⚠  页面内容非常少，可能有问题！');
        }
    });
});

req.on('error', (e) => {
    console.error('❌ 请求失败:', e.message);
});

req.setTimeout(5000, () => {
    req.destroy();
    console.error('❌ 请求超时');
});

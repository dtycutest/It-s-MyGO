const http = require('http');

console.log('=== 页面诊断工具开始 ===\n');
const SERVER_URL = 'http://localhost:5177';

console.log(`1/5 尝试连接 ${SERVER_URL}...`);

// 测试 1: 检查服务器是否在线
async function checkServer() {
  return new Promise((resolve, reject) => {
    const req = http.get(SERVER_URL, (res) => {
      console.log(`   ✓ 服务器响应: ${res.statusCode}`);
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({ status: res.statusCode, body: data });
      });
    });
    
    req.on('error', (err) => {
      console.log(`   ✗ 无法连接服务器:`, err.message);
      resolve({ error: err });
    });
    
    req.setTimeout(5000, () => {
      req.destroy();
      resolve({ error: new Error('请求超时') });
    });
  });
}

// 测试 2: 分析页面内容
function analyzeContent(html) {
  console.log('\n2/5 分析页面内容...');
  
  const hasBody = html.includes('<body');
  const hasContent = html.length > 100;
  const hasTitle = html.includes('<title');
  const hasScript = html.includes('<script');
  
  console.log(`   页面长度: ${html.length} 字符`);
  console.log(`   包含 body: ${hasBody ? '是' : '否'}`);
  console.log(`   包含 title: ${hasTitle ? '是' : '否'}`);
  console.log(`   包含 script: ${hasScript ? '是' : '否'}`);
  
  // 查找内容关键词
  const keywords = ['首页', '测试', '页面', '商品'];
  const foundKeywords = keywords.filter(k => html.includes(k));
  if (foundKeywords.length > 0) {
    console.log(`   找到关键词: ${foundKeywords.join(', ')}`);
  } else {
    console.log(`   ⚠ 未找到预期内容关键词`);
  }
  
  return { hasBody, hasContent, hasTitle, hasScript, foundKeywords };
}

// 测试 3: 检查项目文件
async function checkProject() {
  console.log('\n3/5 检查项目基础...');
  const fs = require('fs');
  const path = require('path');
  
  const indexPath = path.join(__dirname, 'src', 'pages', 'index', 'index.vue');
  
  if (fs.existsSync(indexPath)) {
    const content = fs.readFileSync(indexPath, 'utf8');
    console.log(`   ✓ 找到 index.vue`);
    console.log(`   文件大小: ${content.length} 字符`);
    
    if (content.includes('template') && content.includes('script')) {
      console.log(`   ✓ 页面有 template 和 script`);
    } else {
      console.log(`   ⚠ 页面结构可能不完整`);
    }
  } else {
    console.log(`   ✗ 找不到 index.vue`);
  }
}

// 主流程
async function main() {
  try {
    // 测试 1: 服务器
    const serverResult = await checkServer();
    
    if (serverResult.error) {
      console.log('\n✗ 错误: 无法连接到开发服务器');
      console.log('请确保开发服务器正在运行: npm run dev:h5');
      process.exit(1);
    }
    
    // 测试 2: 内容分析
    const analysis = analyzeContent(serverResult.body);
    
    // 测试 3: 项目检查
    await checkProject();
    
    // 测试 4: 测试独立页面
    console.log('\n4/5 验证独立页面...');
    const purePath = require('path').join(__dirname, 'pure-test.html');
    if (require('fs').existsSync(purePath)) {
      console.log(`   ✓ 独立测试页已创建: pure-test.html`);
      console.log(`   建议: 直接在浏览器打开这个文件测试`);
    }
    
    // 测试 5: 最终建议
    console.log('\n5/5 诊断完成，建议:');
    
    if (!analysis.hasContent) {
      console.log('   1. 先打开 pure-test.html，确认浏览器渲染正常');
      console.log('   2. 如果 pure-test.html 正常，再检查 uni-app 项目');
    } else {
      console.log('   1. 打开浏览器开发者工具 (F12)');
      console.log('   2. 检查 Console 和 Network 标签页');
      console.log('   3. 查看是否有任何错误');
    }
    
    console.log('\n=== 诊断工具结束 ===');
    
  } catch (e) {
    console.error('\n✗ 诊断过程出错:', e);
  }
}

main();

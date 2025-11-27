/**
 * 浏览器Console诊断脚本
 * 在浏览器开发者工具Console中粘贴并运行此脚本
 */

console.log('='.repeat(60));
console.log('🔍 会话标签显示诊断');
console.log('='.repeat(60));

// 1. 检查API返回的会话数据
console.log('\n【步骤1】检查API返回的会话数据...');
fetch('http://localhost:8000/api/sessions?limit=5')
  .then(res => res.json())
  .then(data => {
    const sessions = data.data.sessions;
    console.log(`✅ 获取到 ${sessions.length} 个会话`);

    const sessionWithTags = sessions.find(s => s.tags && s.tags.length > 0);
    if (sessionWithTags) {
      console.log('\n找到带标签的会话:');
      console.log(`  会话名称: ${sessionWithTags.session_name}`);
      console.log(`  标签字段: ${JSON.stringify(sessionWithTags.tags)}`);
      console.log(`  标签数量: ${sessionWithTags.tags.length}`);
    } else {
      console.warn('⚠️  未找到带标签的会话');
    }
  })
  .catch(err => console.error('❌ 获取会话失败:', err));

// 2. 检查标签API
console.log('\n【步骤2】检查标签API...');
const token = localStorage.getItem('access_token');
if (!token) {
  console.error('❌ 未找到登录Token，请先登录');
} else {
  fetch('http://localhost:8000/api/tags', {
    headers: { 'Authorization': `Bearer ${token}` }
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        const systemTags = data.data.system_tags || [];
        const customTags = data.data.custom_tags || [];
        const allTags = [...systemTags, ...customTags];
        console.log(`✅ 标签列表加载成功: ${allTags.length} 个`);
        console.log('  系统标签:', systemTags.map(t => `${t.id}(${t.name})`).join(', '));

        // 存储到全局变量供检查
        window.__DEBUG_TAGS__ = allTags;
      } else {
        console.error('❌ 标签API返回失败:', data);
      }
    })
    .catch(err => console.error('❌ 获取标签失败:', err));
}

// 3. 检查Vue组件状态
console.log('\n【步骤3】等待3秒后检查Vue组件状态...');
setTimeout(() => {
  console.log('\n检查Vue DevTools...');
  console.log('请在Vue DevTools中检查:');
  console.log('  1. Dashboard组件的 allTags 数据');
  console.log('  2. SessionList组件是否收到 allTags prop');
  console.log('  3. SessionList组件的 sessions 数据中是否包含 tags 字段');
  console.log('\n如果Vue DevTools未安装，请安装: https://devtools.vuejs.org/');
}, 3000);

console.log('\n' + '='.repeat(60));
console.log('诊断脚本已启动，请等待结果输出...');
console.log('='.repeat(60));

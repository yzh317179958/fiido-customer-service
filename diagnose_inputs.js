/**
 * 诊断脚本 - 查找页面上的输入框
 * 请在 Coze 页面点击一次 "Add value" 后运行此脚本
 */

(function() {
  console.clear();
  console.log('🔍 开始诊断页面输入框...\n');

  // 1. 尝试多种选择器
  var selectors = [
    'input',
    'textarea',
    'input[type="text"]',
    'input[class*="input"]',
    'textarea[class*="textarea"]',
    '[contenteditable="true"]',
    '[role="textbox"]',
    'input, textarea',
    '*[class*="input"]',
    '*[class*="Input"]'
  ];

  selectors.forEach(function(selector) {
    var elements = document.querySelectorAll(selector);
    if (elements.length > 0) {
      console.log('✅ 选择器:', selector);
      console.log('   找到数量:', elements.length);
      console.log('   示例元素:', elements[0]);
      console.log('   所有元素:', elements);
      console.log('---');
    } else {
      console.log('❌ 选择器:', selector, '(找到 0 个)');
    }
  });

  // 2. 查找所有可能的表单元素
  console.log('\n📋 所有表单相关元素:');
  var allFormElements = document.querySelectorAll('input, textarea, select, [contenteditable]');
  console.log('总数:', allFormElements.length);
  allFormElements.forEach(function(el, index) {
    console.log(index + ':', el.tagName, el.type, el.className, el);
  });

  // 3. 查找最近添加的行
  console.log('\n🔎 查找表格行结构:');
  var rows = document.querySelectorAll('tr, div[class*="row"], div[class*="Row"]');
  console.log('找到行数:', rows.length);
  if (rows.length > 0) {
    var lastRow = rows[rows.length - 1];
    console.log('最后一行:', lastRow);
    console.log('最后一行内的输入框:', lastRow.querySelectorAll('input, textarea, [contenteditable]'));
  }

  console.log('\n✅ 诊断完成！请查看上述信息');
})();

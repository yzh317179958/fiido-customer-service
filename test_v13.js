/**
 * v13.0: 基于 v7.0 + 创建文本节点
 * 关键发现：手动输入过的输入框有 childNodes[#text]
 */

(function() {
  console.clear();
  console.log('🎯 v13.0: 创建文本节点 + innerText 填充\n');

  var testQuestion = 'v13测试问题';
  var testAnswer = 'v13测试答案';

  // 1. 找到输入框
  var rows = document.querySelectorAll('tr.semi-table-row');
  if (rows.length === 0) {
    console.error('❌ 找不到表格行');
    return;
  }

  var lastRow = rows[rows.length - 1];
  var cells = lastRow.querySelectorAll('td.semi-table-row-cell');
  var questionDiv = cells[0].querySelector('div.text-content');
  var answerDiv = cells[1].querySelector('div.text-content');

  console.log('✅ 找到输入框');

  // 2. 填充函数：先创建文本节点，再填充
  function fillWithTextNode(element, text, label) {
    console.log('\n' + label + ':');

    // 检查当前子节点
    console.log('  当前子节点:', element.childNodes.length);

    // 步骤1: 如果没有文本节点，创建一个
    if (element.childNodes.length === 0) {
      console.log('  1️⃣ 创建文本节点');
      var textNode = document.createTextNode('');
      element.appendChild(textNode);
      console.log('  ✓ 文本节点已创建');
    }

    // 步骤2: 填充内容
    console.log('  2️⃣ 填充内容:', text);
    element.innerText = text;

    // 步骤3: 触发事件
    console.log('  3️⃣ 触发事件');
    var events = [
      new FocusEvent('focus', { bubbles: true }),
      new InputEvent('input', {
        bubbles: true,
        cancelable: true,
        inputType: 'insertText',
        data: text
      }),
      new Event('change', { bubbles: true }),
      new FocusEvent('blur', { bubbles: true })
    ];

    events.forEach(function(event) {
      element.dispatchEvent(event);
    });

    console.log('  ✅ 完成');
    console.log('    最终 innerText:', element.innerText);
    console.log('    子节点数:', element.childNodes.length);
  }

  // 3. 顺序填充
  setTimeout(function() {
    console.log('🚀 开始填充...');

    fillWithTextNode(questionDiv, testQuestion, '📝 问题框');

    setTimeout(function() {
      fillWithTextNode(answerDiv, testAnswer, '📝 答案框');

      setTimeout(function() {
        console.log('\n' + '='.repeat(60));
        console.log('✅ 全部完成！');
        console.log('='.repeat(60));
        console.log('📋 填充结果:');
        console.log('  问题:', questionDiv.innerText);
        console.log('  答案:', answerDiv.innerText);
        console.log('\n🔍 请检查:');
        console.log('  1. 页面上是否显示文字？');
        console.log('  2. ⭐⭐⭐ Confirm 按钮是否可点击？');
        console.log('='.repeat(60));
      }, 300);

    }, 300);

  }, 500);

  console.log('⏳ 0.5秒后开始...');

})();

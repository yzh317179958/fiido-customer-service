/**
 * 最终测试：先点击激活，再填充数据
 */

(function() {
  console.clear();
  console.log('🎯 最终测试：点击激活 + 填充数据\n');

  var testQuestion = '最终测试问题';
  var testAnswer = '最终测试答案';

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

  // 2. 核心函数：点击激活 + 填充
  function clickAndFill(element, text) {
    console.log('\n📝 处理输入框...');

    // 步骤1: 点击激活（触发 React 的 onClick 事件）
    console.log('  1️⃣ 点击激活输入框');
    element.click();

    // 等待一下让 React 处理点击
    return new Promise(function(resolve) {
      setTimeout(function() {
        console.log('  2️⃣ 填充数据:', text.substring(0, 20) + '...');

        // 步骤2: 填充数据
        element.innerText = text;

        // 步骤3: 触发所有必要事件
        console.log('  3️⃣ 触发事件');

        // Focus 事件
        element.dispatchEvent(new FocusEvent('focus', { bubbles: true }));

        // Input 事件（最重要）
        element.dispatchEvent(new InputEvent('input', {
          bubbles: true,
          cancelable: true,
          inputType: 'insertText',
          data: text
        }));

        // Change 事件
        element.dispatchEvent(new Event('change', { bubbles: true }));

        // Blur 事件
        element.dispatchEvent(new FocusEvent('blur', { bubbles: true }));

        console.log('  ✅ 完成');
        resolve();

      }, 300); // 等待 300ms 让 React 处理点击
    });
  }

  // 3. 顺序执行：先问题，再答案
  setTimeout(function() {
    console.log('🚀 开始填充流程...');

    clickAndFill(questionDiv, testQuestion).then(function() {
      // 问题填充完成，填充答案
      return clickAndFill(answerDiv, testAnswer);

    }).then(function() {
      // 全部完成
      console.log('\n' + '='.repeat(60));
      console.log('✅ 全部完成！');
      console.log('='.repeat(60));
      console.log('📋 填充内容:');
      console.log('  问题:', questionDiv.innerText);
      console.log('  答案:', answerDiv.innerText);
      console.log('\n🔍 请检查:');
      console.log('  1. 页面上是否显示了文字？');
      console.log('  2. ⭐ Confirm 按钮是否可点击？');
      console.log('='.repeat(60));
    });

  }, 500);

  console.log('⏳ 0.5秒后开始执行...');

})();

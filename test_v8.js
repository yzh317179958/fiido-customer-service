/**
 * v8.0 测试：点击后等待更长时间再填充
 */

(function() {
  console.clear();
  console.log('🎯 v8.0 测试：延长等待时间\n');

  var testQuestion = 'v8测试问题';
  var testAnswer = 'v8测试答案';

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

  // 2. 改进的填充函数
  function clickAndFill(element, text, label) {
    return new Promise(function(resolve) {
      console.log('\n' + label + ':');
      console.log('  1️⃣ 点击激活...');

      // 步骤1: 点击
      element.click();

      // 步骤2: 等待 800ms（更长时间）
      setTimeout(function() {
        console.log('  2️⃣ 检查状态...');
        console.log('    当前 innerText:', element.innerText);
        console.log('    当前 innerHTML:', element.innerHTML);

        // 步骤3: 填充数据
        console.log('  3️⃣ 填充数据:', text);
        element.innerText = text;

        // 步骤4: 触发事件
        setTimeout(function() {
          console.log('  4️⃣ 触发事件...');

          // 触发 input 事件（最关键）
          var inputEvent = new InputEvent('input', {
            bubbles: true,
            cancelable: true,
            inputType: 'insertText',
            data: text
          });
          element.dispatchEvent(inputEvent);

          // 触发 change 事件
          element.dispatchEvent(new Event('change', { bubbles: true }));

          // 检查结果
          setTimeout(function() {
            console.log('  ✅ 完成');
            console.log('    最终 innerText:', element.innerText);
            resolve();
          }, 200);

        }, 200); // 填充后等待 200ms 再触发事件

      }, 800); // 点击后等待 800ms 再填充

    });
  }

  // 3. 顺序执行
  setTimeout(function() {
    console.log('🚀 开始填充流程...');

    clickAndFill(questionDiv, testQuestion, '📝 问题框').then(function() {
      // 问题完成，填充答案
      return clickAndFill(answerDiv, testAnswer, '📝 答案框');

    }).then(function() {
      // 全部完成
      console.log('\n' + '='.repeat(60));
      console.log('✅ 全部完成！');
      console.log('='.repeat(60));
      console.log('📋 检查结果:');
      console.log('  问题 innerText:', questionDiv.innerText);
      console.log('  答案 innerText:', answerDiv.innerText);
      console.log('\n🔍 请检查页面:');
      console.log('  1. 两个输入框是否都有文字显示？');
      console.log('  2. ⭐ Confirm 按钮是否可点击（变蓝）？');
      console.log('='.repeat(60));
    });

  }, 500);

  console.log('⏳ 0.5秒后开始执行...');

})();

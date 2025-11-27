/**
 * v11.0: 模拟手动输入来初始化输入框
 * 策略：输入一个字符 → 全选 → 删除 → 再填充真实内容
 */

(function() {
  console.clear();
  console.log('🎯 v11.0: 模拟手动输入初始化\n');

  var testQuestion = 'v11测试问题完整版';
  var testAnswer = 'v11测试答案完整版';

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

  // 2. 模拟手动初始化 + 填充
  function initializeAndFill(element, text, label) {
    return new Promise(function(resolve) {
      console.log('\n' + label + ':');

      // 步骤1: 点击输入框
      console.log('  1️⃣ 点击输入框');
      element.click();

      setTimeout(function() {
        // 步骤2: 模拟输入一个字符（初始化）
        console.log('  2️⃣ 模拟输入字符"a"（初始化）');

        element.innerText = 'a';

        // 触发 input 事件
        var inputEvent = new InputEvent('input', {
          bubbles: true,
          cancelable: true,
          inputType: 'insertText',
          data: 'a'
        });
        element.dispatchEvent(inputEvent);

        setTimeout(function() {
          // 步骤3: 全选并替换为真实内容
          console.log('  3️⃣ 替换为真实内容');

          element.innerText = text;

          // 触发 input 事件（表示内容变化）
          var replaceEvent = new InputEvent('input', {
            bubbles: true,
            cancelable: true,
            inputType: 'insertText',
            data: text
          });
          element.dispatchEvent(replaceEvent);

          setTimeout(function() {
            // 步骤4: 触发 change 和 blur
            console.log('  4️⃣ 触发 change 和 blur');

            element.dispatchEvent(new Event('change', { bubbles: true }));
            element.dispatchEvent(new FocusEvent('blur', { bubbles: true }));

            console.log('  ✅ 完成');
            console.log('    最终内容:', element.innerText);

            resolve();

          }, 200);

        }, 200);

      }, 300);

    });
  }

  // 3. 顺序执行
  setTimeout(function() {
    console.log('🚀 开始填充流程...');

    initializeAndFill(questionDiv, testQuestion, '📝 问题框').then(function() {
      return initializeAndFill(answerDiv, testAnswer, '📝 答案框');

    }).then(function() {
      console.log('\n' + '='.repeat(60));
      console.log('✅ 全部完成！');
      console.log('='.repeat(60));
      console.log('📋 填充结果:');
      console.log('  问题:', questionDiv.innerText);
      console.log('  答案:', answerDiv.innerText);
      console.log('\n🔍 请检查:');
      console.log('  1. 页面上是否显示文字？');
      console.log('  2. 点击输入框，内容是否保留（不被清空）？');
      console.log('  3. ⭐⭐⭐ Confirm 按钮是否可点击？');
      console.log('='.repeat(60));
    });

  }, 500);

  console.log('⏳ 0.5秒后开始...');

})();

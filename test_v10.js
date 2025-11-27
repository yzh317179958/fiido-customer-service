/**
 * v10.0: 点击后等待进入编辑模式，再填充
 * 关键：检测输入框是否真正激活（可能通过 contenteditable 属性变化）
 */

(function() {
  console.clear();
  console.log('🎯 v10.0: 检测编辑模式 + 填充\n');

  var testQuestion = 'v10测试问题';
  var testAnswer = 'v10测试答案';

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

  // 2. 检测并等待编辑模式激活
  function waitForEditable(element) {
    return new Promise(function(resolve) {
      console.log('  🔍 检测编辑状态...');
      console.log('    contentEditable:', element.contentEditable);
      console.log('    getAttribute:', element.getAttribute('contenteditable'));

      var checkInterval = setInterval(function() {
        // 检查是否变成可编辑
        if (element.contentEditable === 'true' ||
            element.contentEditable === 'plaintext-only' ||
            element.getAttribute('contenteditable') === 'true') {
          console.log('  ✅ 已进入编辑模式！');
          clearInterval(checkInterval);
          resolve();
        }
      }, 50); // 每 50ms 检查一次

      // 超时保护：2秒后强制继续
      setTimeout(function() {
        console.log('  ⚠️  超时，强制继续');
        clearInterval(checkInterval);
        resolve();
      }, 2000);
    });
  }

  // 3. 完整的点击 + 等待 + 填充流程
  function clickWaitAndFill(element, text, label) {
    return new Promise(function(resolve) {
      console.log('\n' + label + ':');
      console.log('  1️⃣ 点击输入框...');

      // 点击
      element.click();

      // 等待进入编辑模式
      waitForEditable(element).then(function() {
        console.log('  2️⃣ 填充数据:', text);

        // 使用 innerText 填充
        element.innerText = text;

        // 触发事件
        console.log('  3️⃣ 触发事件...');
        var events = [
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

        resolve();
      });
    });
  }

  // 4. 顺序执行
  setTimeout(function() {
    console.log('🚀 开始填充流程...');

    clickWaitAndFill(questionDiv, testQuestion, '📝 问题框').then(function() {
      // 问题完成，填充答案
      return clickWaitAndFill(answerDiv, testAnswer, '📝 答案框');

    }).then(function() {
      // 全部完成
      console.log('\n' + '='.repeat(60));
      console.log('✅ 全部完成！');
      console.log('='.repeat(60));
      console.log('📋 填充结果:');
      console.log('  问题:', questionDiv.innerText);
      console.log('  答案:', answerDiv.innerText);
      console.log('\n🔍 请检查:');
      console.log('  1. 页面上是否显示文字？');
      console.log('  2. 单击输入框，内容是否保留（不被清空）？');
      console.log('  3. ⭐⭐⭐ Confirm 按钮是否可点击？');
      console.log('='.repeat(60));
    });

  }, 500);

  console.log('⏳ 0.5秒后开始...');

})();

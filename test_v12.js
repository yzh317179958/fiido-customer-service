/**
 * v12.0: 完全模拟键盘逐字输入
 * 不使用 innerText 赋值，真正模拟用户打字
 */

(function() {
  console.clear();
  console.log('🎯 v12.0: 完全模拟键盘输入\n');

  var testQuestion = 'ABC';  // 先测试短文本
  var testAnswer = 'XYZ';

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

  // 2. 模拟真实的键盘输入
  function typeCharacter(element, char) {
    // 先让元素获得焦点
    element.focus();

    // 模拟 keydown
    var keydownEvent = new KeyboardEvent('keydown', {
      key: char,
      code: 'Key' + char.toUpperCase(),
      keyCode: char.charCodeAt(0),
      which: char.charCodeAt(0),
      bubbles: true,
      cancelable: true,
      composed: true
    });
    element.dispatchEvent(keydownEvent);

    // 模拟 beforeinput
    var beforeInputEvent = new InputEvent('beforeinput', {
      bubbles: true,
      cancelable: true,
      inputType: 'insertText',
      data: char
    });
    element.dispatchEvent(beforeInputEvent);

    // 实际插入字符（关键）
    element.innerText = element.innerText + char;

    // 模拟 input 事件（最重要）
    var inputEvent = new InputEvent('input', {
      bubbles: true,
      cancelable: true,
      inputType: 'insertText',
      data: char
    });
    element.dispatchEvent(inputEvent);

    // 模拟 keyup
    var keyupEvent = new KeyboardEvent('keyup', {
      key: char,
      code: 'Key' + char.toUpperCase(),
      keyCode: char.charCodeAt(0),
      which: char.charCodeAt(0),
      bubbles: true,
      cancelable: true,
      composed: true
    });
    element.dispatchEvent(keyupEvent);
  }

  // 3. 逐字输入完整文本
  function typeText(element, text, label) {
    return new Promise(function(resolve) {
      console.log('\n' + label + ':');
      console.log('  准备输入:', text);

      // 点击激活
      element.click();

      setTimeout(function() {
        console.log('  开始逐字输入...');

        var index = 0;

        function typeNext() {
          if (index >= text.length) {
            // 输入完成
            console.log('  ✅ 输入完成:', element.innerText);

            // 触发 change 和 blur
            element.dispatchEvent(new Event('change', { bubbles: true }));
            element.dispatchEvent(new FocusEvent('blur', { bubbles: true }));

            resolve();
            return;
          }

          var char = text[index];
          console.log('    输入字符 [' + index + ']:', char);

          typeCharacter(element, char);

          index++;

          // 每个字符间隔 50ms（模拟真实打字速度）
          setTimeout(typeNext, 50);
        }

        typeNext();

      }, 300);

    });
  }

  // 4. 顺序执行
  setTimeout(function() {
    console.log('🚀 开始模拟输入...');

    typeText(questionDiv, testQuestion, '📝 问题框').then(function() {
      return typeText(answerDiv, testAnswer, '📝 答案框');

    }).then(function() {
      console.log('\n' + '='.repeat(60));
      console.log('✅ 全部完成！');
      console.log('='.repeat(60));
      console.log('📋 填充结果:');
      console.log('  问题:', questionDiv.innerText);
      console.log('  答案:', answerDiv.innerText);
      console.log('\n🔍 请检查:');
      console.log('  1. 页面上是否显示 "ABC" 和 "XYZ"？');
      console.log('  2. 点击输入框，内容是否保留？');
      console.log('  3. ⭐⭐⭐ Confirm 按钮是否可点击？');
      console.log('='.repeat(60));
    });

  }, 500);

  console.log('⏳ 0.5秒后开始...');
  console.log('⚠️  这次会逐字输入，会比较慢（每字 50ms）');

})();

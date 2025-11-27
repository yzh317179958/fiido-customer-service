/**
 * React 专用填充测试脚本
 * 尝试直接修改 React Fiber 来更新数据
 */

(function() {
  console.clear();
  console.log('🧪 React Fiber 填充测试...\n');

  // 测试数据
  var testQuestion = '测试问题 React Fiber';
  var testAnswer = '测试答案 React Fiber';

  // 1. 找到最后一行
  var rows = document.querySelectorAll('tr.semi-table-row');
  if (rows.length === 0) {
    console.error('❌ 找不到表格行');
    return;
  }

  var lastRow = rows[rows.length - 1];
  var cells = lastRow.querySelectorAll('td.semi-table-row-cell');

  if (cells.length < 2) {
    console.error('❌ 单元格不足');
    return;
  }

  var questionDiv = cells[0].querySelector('div.text-content');
  var answerDiv = cells[1].querySelector('div.text-content');

  console.log('✅ 找到输入框');
  console.log('  问题框:', questionDiv);
  console.log('  答案框:', answerDiv);

  // 2. 尝试方法1: 使用 React Fiber 的 memoizedProps
  console.log('\n🔧 方法1: 修改 React Fiber');

  function tryReactFiberUpdate(div, value) {
    var reactKey = Object.keys(div).find(key =>
      key.startsWith('__reactFiber') ||
      key.startsWith('__reactInternalInstance')
    );

    if (!reactKey) {
      console.log('  ❌ 未找到 React Fiber key');
      return false;
    }

    var fiber = div[reactKey];
    console.log('  ✅ 找到 Fiber:', fiber);

    // 尝试修改 memoizedProps
    if (fiber.memoizedProps) {
      console.log('  ✅ 找到 memoizedProps:', fiber.memoizedProps);
      if (fiber.memoizedProps.value !== undefined) {
        fiber.memoizedProps.value = value;
        console.log('  ✅ 设置 memoizedProps.value =', value);
      }
    }

    return true;
  }

  tryReactFiberUpdate(questionDiv, testQuestion);
  tryReactFiberUpdate(answerDiv, testAnswer);

  // 3. 方法2: 模拟用户输入（最强力）
  console.log('\n🔧 方法2: 模拟用户键盘输入');

  function simulateUserInput(element, text) {
    // 先清空
    element.innerText = '';

    // 聚焦
    element.focus();
    element.dispatchEvent(new FocusEvent('focus', { bubbles: true }));

    // 模拟逐字输入
    for (var i = 0; i < text.length; i++) {
      var char = text[i];

      // 模拟 keydown
      var keydownEvent = new KeyboardEvent('keydown', {
        key: char,
        code: 'Key' + char.toUpperCase(),
        bubbles: true,
        cancelable: true
      });
      element.dispatchEvent(keydownEvent);

      // 添加字符
      element.innerText += char;

      // 模拟 input 事件
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
        bubbles: true,
        cancelable: true
      });
      element.dispatchEvent(keyupEvent);
    }

    // 触发 change 和 blur
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new FocusEvent('blur', { bubbles: true }));

    console.log('  ✅ 模拟输入完成:', text.substring(0, 20) + '...');
  }

  // 只模拟前几个字符，避免太慢
  var shortQuestion = testQuestion.substring(0, 5);
  var shortAnswer = testAnswer.substring(0, 5);

  setTimeout(function() {
    console.log('\n开始模拟输入问题...');
    simulateUserInput(questionDiv, shortQuestion);

    setTimeout(function() {
      console.log('开始模拟输入答案...');
      simulateUserInput(answerDiv, shortAnswer);

      setTimeout(function() {
        console.log('\n✅ 全部完成！请检查:');
        console.log('1. 页面上是否显示文字？');
        console.log('2. Confirm 按钮是否可点击？');
      }, 500);

    }, 500);

  }, 1000);

  console.log('\n⏳ 1秒后开始测试...');

})();

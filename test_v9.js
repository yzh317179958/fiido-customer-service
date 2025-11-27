/**
 * v9.0: 基于 v7.0，不点击，只填充 + 强化事件触发
 * 目标：让 React 识别到数据变化，通过表单验证
 */

(function() {
  console.clear();
  console.log('🎯 v9.0: 强化事件触发（不点击）\n');

  var testQuestion = 'v9测试问题ABC123';
  var testAnswer = 'v9测试答案XYZ789';

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

  // 2. 强化版填充函数（不点击）
  function fillWithStrongEvents(element, text, label) {
    console.log('\n' + label + ':');
    console.log('  1️⃣ 填充数据:', text);

    // 直接填充（像 v7.0 那样）
    element.innerText = text;

    console.log('  2️⃣ 触发所有可能的事件...');

    // 触发超级多的事件，确保 React 能检测到
    var events = [
      // 焦点事件
      new FocusEvent('focus', { bubbles: true }),
      new FocusEvent('focusin', { bubbles: true }),

      // 输入事件（最关键）
      new InputEvent('input', {
        bubbles: true,
        cancelable: true,
        inputType: 'insertText',
        data: text
      }),
      new Event('input', { bubbles: true }),

      // 变化事件
      new Event('change', { bubbles: true }),

      // 键盘事件
      new KeyboardEvent('keydown', { bubbles: true, key: 'Enter' }),
      new KeyboardEvent('keyup', { bubbles: true, key: 'Enter' }),

      // 失焦事件
      new FocusEvent('blur', { bubbles: true }),
      new FocusEvent('focusout', { bubbles: true })
    ];

    events.forEach(function(event) {
      element.dispatchEvent(event);
    });

    // 3. 额外尝试：直接修改 React Fiber 的 props
    var reactKey = Object.keys(element).find(function(key) {
      return key.startsWith('__reactFiber') || key.startsWith('__reactInternalInstance');
    });

    if (reactKey) {
      var fiber = element[reactKey];
      console.log('  3️⃣ 尝试修改 React Fiber...');

      // 尝试触发 React 的更新
      if (fiber.return && fiber.return.stateNode) {
        console.log('    找到父组件 stateNode');
      }

      // 强制触发 React 的 onChange（如果有）
      if (fiber.memoizedProps && fiber.memoizedProps.onChange) {
        console.log('    触发 onChange 回调');
        try {
          fiber.memoizedProps.onChange({ target: element });
        } catch (e) {
          console.log('    onChange 调用失败:', e.message);
        }
      }
    }

    console.log('  ✅ 完成');
    console.log('    最终 innerText:', element.innerText);
  }

  // 3. 顺序填充
  setTimeout(function() {
    console.log('🚀 开始填充...');

    fillWithStrongEvents(questionDiv, testQuestion, '📝 问题框');

    setTimeout(function() {
      fillWithStrongEvents(answerDiv, testAnswer, '📝 答案框');

      setTimeout(function() {
        console.log('\n' + '='.repeat(60));
        console.log('✅ 全部完成！');
        console.log('='.repeat(60));
        console.log('📋 填充结果:');
        console.log('  问题:', questionDiv.innerText);
        console.log('  答案:', answerDiv.innerText);
        console.log('\n🔍 请检查:');
        console.log('  1. 页面上是否显示文字？ ← 应该显示');
        console.log('  2. ⭐⭐⭐ Confirm 按钮是否可点击？');
        console.log('='.repeat(60));
      }, 500);

    }, 500);

  }, 500);

  console.log('⏳ 0.5秒后开始...');

})();

/**
 * v14.0: 通过 React Fiber 直接修改组件状态
 *
 * 关键发现：脚本填充的数据只在 DOM 上显示，但没有保存到 React 状态
 * 解决方案：找到 React Fiber 节点并直接修改 memoizedProps.value
 */

(function() {
  console.clear();
  console.log('🎯 v14.0: React Fiber 状态修改方式\n');

  var testQuestion = 'v14测试问题';
  var testAnswer = 'v14测试答案';

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

  // 2. 通过 React Fiber 修改状态
  function fillViaReactFiber(element, text, label) {
    console.log('\n' + label + ':');

    // 步骤1: 找到 React Fiber
    var reactKey = Object.keys(element).find(function(k) {
      return k.startsWith('__reactFiber') || k.startsWith('__reactInternal');
    });

    if (!reactKey) {
      console.error('  ❌ 未找到 React Fiber');
      return false;
    }

    console.log('  ✅ 找到 React Fiber');

    var fiber = element[reactKey];

    // 步骤2: 遍历 Fiber 树找到输入组件
    var currentFiber = fiber;
    var targetFiber = null;
    var depth = 0;

    while (currentFiber && depth < 15) {
      // 查找有 value 或 onChange 的节点（通常是受控组件）
      if (currentFiber.memoizedProps &&
          (currentFiber.memoizedProps.value !== undefined ||
           currentFiber.memoizedProps.onChange)) {

        console.log('  🎯 找到目标 Fiber (层级 ' + depth + '):');
        console.log('    type:', currentFiber.type);
        console.log('    tag:', currentFiber.tag);
        console.log('    当前 value:', currentFiber.memoizedProps.value);

        targetFiber = currentFiber;
        break;
      }

      currentFiber = currentFiber.return;
      depth++;
    }

    if (!targetFiber) {
      console.warn('  ⚠️  未找到目标 Fiber，尝试直接修改 DOM');

      // 回退方案：直接修改 DOM
      element.innerText = text;

      // 触发事件
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

      return false;
    }

    // 步骤3: 修改 React 状态
    console.log('  📝 修改 React 状态...');

    // 修改 memoizedProps.value
    if (targetFiber.memoizedProps) {
      targetFiber.memoizedProps.value = text;
      console.log('    ✓ memoizedProps.value 已更新');
    }

    // 修改 pendingProps.value
    if (targetFiber.pendingProps) {
      targetFiber.pendingProps.value = text;
      console.log('    ✓ pendingProps.value 已更新');
    }

    // 步骤4: 同时修改 DOM（保证显示）
    element.innerText = text;
    console.log('    ✓ DOM innerText 已更新');

    // 步骤5: 触发 onChange 回调（如果存在）
    if (targetFiber.memoizedProps && targetFiber.memoizedProps.onChange) {
      console.log('  🔔 触发 onChange 回调...');

      // 构造合成事件对象
      var syntheticEvent = {
        target: {
          value: text
        },
        currentTarget: {
          value: text
        },
        nativeEvent: new InputEvent('input', {
          bubbles: true,
          cancelable: true,
          inputType: 'insertText',
          data: text
        })
      };

      try {
        targetFiber.memoizedProps.onChange(syntheticEvent);
        console.log('    ✓ onChange 回调已执行');
      } catch (e) {
        console.error('    ❌ onChange 回调失败:', e.message);
      }
    }

    // 步骤6: 触发 React 更新
    console.log('  🔄 触发 React 更新...');

    // 标记 Fiber 需要更新
    var root = targetFiber;
    while (root.return) {
      root = root.return;
    }

    // 触发标准事件（让 React 检测到变化）
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
    console.log('    React value:', targetFiber.memoizedProps.value);

    return true;
  }

  // 3. 顺序填充
  setTimeout(function() {
    console.log('🚀 开始填充...');

    fillViaReactFiber(questionDiv, testQuestion, '📝 问题框');

    setTimeout(function() {
      fillViaReactFiber(answerDiv, testAnswer, '📝 答案框');

      setTimeout(function() {
        console.log('\n' + '='.repeat(60));
        console.log('✅ 全部完成！');
        console.log('='.repeat(60));
        console.log('📋 填充结果:');
        console.log('  问题:', questionDiv.innerText);
        console.log('  答案:', answerDiv.innerText);
        console.log('\n🔍 请检查:');
        console.log('  1. 页面上是否显示文字？');
        console.log('  2. 点击编辑按钮，Field value 是否有内容？⭐⭐⭐');
        console.log('  3. Confirm 按钮是否可点击？');
        console.log('='.repeat(60));
      }, 300);

    }, 300);

  }, 500);

  console.log('⏳ 0.5秒后开始...');

})();

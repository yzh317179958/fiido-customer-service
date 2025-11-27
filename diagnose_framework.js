/**
 * 诊断脚本 - 找到触发框架验证的正确方式
 * 请手动点击 Add value，然后手动在第一个框输入一些文字，再运行此脚本
 */

(function() {
  console.clear();
  console.log('🔍 诊断框架事件监听...\n');

  // 1. 找到第一行
  var rows = document.querySelectorAll('tr.semi-table-row');
  if (rows.length === 0) {
    console.error('❌ 找不到表格行');
    return;
  }

  var lastRow = rows[rows.length - 1];
  var cells = lastRow.querySelectorAll('td.semi-table-row-cell');
  var questionCell = cells[0];
  var questionDiv = questionCell.querySelector('div.text-content');

  console.log('✅ 找到输入框:', questionDiv);
  console.log('当前内容:', questionDiv.innerText);

  // 2. 监听所有可能的事件
  var eventTypes = [
    'input', 'change', 'blur', 'focus', 'keyup', 'keydown', 'keypress',
    'compositionstart', 'compositionend', 'paste', 'cut',
    'DOMSubtreeModified', 'DOMCharacterDataModified'
  ];

  console.log('\n📝 正在监听以下事件:');
  eventTypes.forEach(function(eventType) {
    questionDiv.addEventListener(eventType, function(e) {
      console.log('🔔 触发事件:', eventType, '| 内容:', questionDiv.innerText);
    });
    console.log('  ✓', eventType);
  });

  console.log('\n⚠️  现在请手动在输入框中输入一些文字');
  console.log('⚠️  观察控制台输出，看哪些事件被触发了');

  // 3. 检查是否有 Vue/React 实例
  console.log('\n🔎 检查框架实例:');

  // 检查 Vue
  if (questionDiv.__vue__) {
    console.log('✅ 发现 Vue 实例:', questionDiv.__vue__);
  } else if (questionDiv.__vueParentComponent) {
    console.log('✅ 发现 Vue3 实例:', questionDiv.__vueParentComponent);
  } else {
    console.log('❌ 未发现 Vue 实例');
  }

  // 检查 React
  var reactKey = Object.keys(questionDiv).find(key =>
    key.startsWith('__reactInternalInstance') ||
    key.startsWith('__reactFiber')
  );
  if (reactKey) {
    console.log('✅ 发现 React 实例:', questionDiv[reactKey]);
  } else {
    console.log('❌ 未发现 React 实例');
  }

  // 4. 尝试直接修改值并触发所有事件
  console.log('\n🧪 测试修改值并触发事件:');

  setTimeout(function() {
    var testValue = '自动测试文本 ' + Date.now();
    console.log('设置值为:', testValue);

    questionDiv.innerText = testValue;

    // 触发所有常用事件
    ['input', 'change', 'blur'].forEach(function(eventType) {
      var event = new Event(eventType, {
        bubbles: true,
        cancelable: true,
        composed: true  // 允许事件穿透 Shadow DOM
      });
      questionDiv.dispatchEvent(event);
      console.log('触发:', eventType);
    });

    console.log('\n✅ 测试完成！请检查:');
    console.log('1. 页面上的值是否变化？');
    console.log('2. Confirm 按钮是否可点击？');

  }, 3000);

  console.log('\n⏳ 3秒后自动执行填充测试...');

})();

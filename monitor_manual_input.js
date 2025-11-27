/**
 * 监控手动输入时的 DOM 变化
 * 请点击 Add value，然后运行此脚本，再手动输入文字
 */

(function() {
  console.clear();
  console.log('🔍 监控 DOM 变化...\n');

  // 1. 找到输入框
  var rows = document.querySelectorAll('tr.semi-table-row');
  var lastRow = rows[rows.length - 1];
  var cells = lastRow.querySelectorAll('td.semi-table-row-cell');
  var questionDiv = cells[0].querySelector('div.text-content');

  console.log('✅ 监控目标:', questionDiv);
  console.log('当前 HTML:', questionDiv.outerHTML);

  // 2. 监控 DOM 变化
  var observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      console.log('\n🔔 DOM 变化:');
      console.log('  类型:', mutation.type);
      console.log('  目标:', mutation.target);

      if (mutation.type === 'childList') {
        console.log('  新增节点:', mutation.addedNodes);
        console.log('  删除节点:', mutation.removedNodes);
      } else if (mutation.type === 'characterData') {
        console.log('  新内容:', mutation.target.textContent);
      } else if (mutation.type === 'attributes') {
        console.log('  属性:', mutation.attributeName);
        console.log('  新值:', mutation.target.getAttribute(mutation.attributeName));
      }

      console.log('  当前 innerHTML:', questionDiv.innerHTML);
      console.log('  当前 innerText:', questionDiv.innerText);
    });
  });

  observer.observe(questionDiv, {
    childList: true,
    characterData: true,
    subtree: true,
    attributes: true,
    attributeOldValue: true,
    characterDataOldValue: true
  });

  console.log('✅ 开始监控...');
  console.log('⚠️  现在请手动点击输入框并输入一些文字');
  console.log('⚠️  观察控制台输出');

  // 3. 同时监控所有事件
  var allEvents = [
    'click', 'dblclick', 'mousedown', 'mouseup',
    'focus', 'blur', 'focusin', 'focusout',
    'input', 'change', 'beforeinput',
    'keydown', 'keyup', 'keypress',
    'compositionstart', 'compositionupdate', 'compositionend'
  ];

  allEvents.forEach(function(eventName) {
    questionDiv.addEventListener(eventName, function(e) {
      console.log('🎯 事件:', eventName, '| innerText:', questionDiv.innerText);
    }, true);
  });

  // 4. 10秒后停止监控
  setTimeout(function() {
    observer.disconnect();
    console.log('\n⏹️  监控已停止');
  }, 10000);

})();

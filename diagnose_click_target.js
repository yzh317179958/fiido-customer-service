/**
 * 诊断：监听点击事件，找到正确的点击目标
 */

(function() {
  console.clear();
  console.log('🔍 监听点击事件...\n');

  // 找到输入区域
  var rows = document.querySelectorAll('tr.semi-table-row');
  var lastRow = rows[rows.length - 1];
  var cells = lastRow.querySelectorAll('td.semi-table-row-cell');
  var questionCell = cells[0];
  var questionDiv = questionCell.querySelector('div.text-content');

  console.log('✅ 监听目标:');
  console.log('  单元格 (td):', questionCell);
  console.log('  文本容器 (div.text-content):', questionDiv);
  console.log('  外层包装:', questionCell.querySelector('div.text-render-wrapper'));

  // 监听整个单元格及其所有子元素的点击
  console.log('\n📝 正在监听点击事件...');

  var elementsToMonitor = [
    questionCell,
    questionCell.querySelector('div.text-render-wrapper'),
    questionDiv
  ];

  elementsToMonitor.forEach(function(element, index) {
    if (!element) return;

    element.addEventListener('click', function(e) {
      console.log('\n🎯 捕获点击事件:');
      console.log('  点击目标:', e.target);
      console.log('  当前元素:', e.currentTarget);
      console.log('  元素类名:', e.target.className);
      console.log('  元素标签:', e.target.tagName);
      console.log('  是否是 text-content:', e.target.classList.contains('text-content'));
      console.log('  事件阶段:', e.eventPhase);

      // 检查点击后的状态变化
      setTimeout(function() {
        console.log('\n点击后状态:');
        console.log('  contentEditable:', questionDiv.contentEditable);
        console.log('  innerText:', questionDiv.innerText);
        console.log('  获取焦点?:', document.activeElement === questionDiv);
      }, 100);

    }, true); // 使用捕获阶段
  });

  console.log('✅ 监听已启动');
  console.log('⚠️  请手动点击输入框，观察控制台输出');
  console.log('⚠️  特别注意：');
  console.log('    1. 实际点击的是哪个元素？');
  console.log('    2. 点击后 contentEditable 是否变化？');
  console.log('    3. 是否有特殊的事件处理？');

})();

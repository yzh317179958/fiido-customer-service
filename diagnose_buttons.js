/**
 * 诊断：查看操作列中两个按钮的详细信息
 */

(function() {
  console.clear();
  console.log('🔍 诊断操作列按钮\n');

  var rows = document.querySelectorAll('tr.semi-table-row');

  if (rows.length === 0) {
    console.error('❌ 找不到表格行');
    return;
  }

  var lastRow = rows[rows.length - 1];
  var cells = lastRow.querySelectorAll('td.semi-table-row-cell');

  if (cells.length < 3) {
    console.error('❌ 单元格不足');
    return;
  }

  var operationCell = cells[2];

  console.log('✅ 找到操作列单元格');

  var buttons = operationCell.querySelectorAll('button');

  console.log('找到 ' + buttons.length + ' 个按钮\n');

  buttons.forEach(function(btn, index) {
    console.log('='.repeat(60));
    console.log('按钮 ' + index + ':');
    console.log('='.repeat(60));
    console.log('  textContent:', btn.textContent.trim() || '(空)');
    console.log('  className:', btn.className);
    console.log('  innerHTML:', btn.innerHTML.substring(0, 200));
    console.log('  title:', btn.title || '(无)');
    console.log('  aria-label:', btn.getAttribute('aria-label') || '(无)');

    // 查找 SVG 图标
    var svg = btn.querySelector('svg');
    if (svg) {
      console.log('  SVG 存在: true');
      console.log('  SVG className:', svg.className.baseVal || svg.className);
      console.log('  data-icon:', svg.getAttribute('data-icon') || '(无)');
    } else {
      console.log('  SVG 存在: false');
    }

    console.log('\n');
  });

  console.log('='.repeat(60));
  console.log('✅ 诊断完成');
  console.log('='.repeat(60));
  console.log('\n请查看两个按钮的差异，找出区分它们的方法');
  console.log('例如: className、title、aria-label、data-icon 等');

})();

/**
 * 深度诊断 - 查找最后一行内的所有可编辑元素
 */

(function() {
  console.clear();
  console.log('🔬 深度诊断最后一行...\n');

  // 1. 找到所有行
  var rows = document.querySelectorAll('tr');
  console.log('📊 找到表格行数:', rows.length);

  if (rows.length === 0) {
    console.error('❌ 没有找到表格行！');
    return;
  }

  // 2. 检查最后一行
  var lastRow = rows[rows.length - 1];
  console.log('✅ 最后一行 HTML:\n', lastRow.outerHTML.substring(0, 500) + '...');
  console.log('\n📝 最后一行完整结构:', lastRow);

  // 3. 查找最后一行内的所有可能输入元素
  console.log('\n🔍 查找最后一行内的元素:');

  var queries = [
    'input',
    'textarea',
    '[contenteditable]',
    'div[contenteditable]',
    '*[contenteditable="true"]',
    '*[contenteditable="false"]',
    'div[role="textbox"]',
    'div[class*="edit"]',
    'div[class*="input"]',
    'td',  // 表格单元格
    'td > *',  // 单元格内的元素
  ];

  queries.forEach(function(query) {
    var elements = lastRow.querySelectorAll(query);
    if (elements.length > 0) {
      console.log('✅', query, '- 找到', elements.length, '个');
      elements.forEach(function(el, i) {
        console.log('  [' + i + ']', el.tagName, 'class:', el.className, 'contenteditable:', el.contentEditable);
        console.log('  ', el);
      });
    } else {
      console.log('❌', query, '- 0 个');
    }
  });

  // 4. 检查所有 td 单元格
  console.log('\n📋 检查所有表格单元格 (td):');
  var cells = lastRow.querySelectorAll('td');
  console.log('单元格数量:', cells.length);
  cells.forEach(function(cell, i) {
    console.log('单元格 [' + i + ']:', cell);
    console.log('  innerHTML:', cell.innerHTML.substring(0, 200));
    console.log('  所有子元素:', cell.children);

    // 检查单元格内的 div
    var divs = cell.querySelectorAll('div');
    console.log('  内部 div 数量:', divs.length);
    divs.forEach(function(div, j) {
      console.log('    div[' + j + '] contentEditable:', div.contentEditable, 'class:', div.className);
    });
  });

  // 5. 尝试查找可编辑区域
  console.log('\n🎯 查找可编辑区域:');
  var editables = lastRow.querySelectorAll('[contenteditable], div');
  editables.forEach(function(el, i) {
    if (el.contentEditable === 'true' || el.contentEditable === 'plaintext-only') {
      console.log('✅ 可编辑元素 [' + i + ']:', el);
      console.log('   contentEditable:', el.contentEditable);
      console.log('   innerText:', el.innerText);
    }
  });

  console.log('\n✅ 诊断完成！');
})();

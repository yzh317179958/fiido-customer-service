/**
 * 对比诊断：找出手动输入过和未输入过的输入框的差异
 *
 * 步骤：
 * 1. 手动点击 Add value 两次（创建2个空行）
 * 2. 在第1行手动输入一些文字（然后全选删除，留空）
 * 3. 第2行不输入（保持空白）
 * 4. 运行此脚本，对比两个输入框的差异
 */

(function() {
  console.clear();
  console.log('🔍 对比诊断：手动输入过 vs 未输入过\n');
  console.log('⚠️  请确保你已经：');
  console.log('  1. 创建了2个空行（点击2次 Add value）');
  console.log('  2. 在第1行手动输入文字然后删除（留空）');
  console.log('  3. 第2行保持空白（不输入）');
  console.log('  4. 然后运行此脚本\n');

  var rows = document.querySelectorAll('tr.semi-table-row');

  if (rows.length < 2) {
    console.error('❌ 至少需要2行！请先创建2个空行');
    return;
  }

  // 倒数第2行（手动输入过）
  var row1 = rows[rows.length - 2];
  var cell1 = row1.querySelectorAll('td.semi-table-row-cell')[0];
  var div1 = cell1.querySelector('div.text-content');

  // 最后1行（未输入过）
  var row2 = rows[rows.length - 1];
  var cell2 = row2.querySelectorAll('td.semi-table-row-cell')[0];
  var div2 = cell2.querySelector('div.text-content');

  console.log('✅ 找到输入框');
  console.log('  第1行（手动输入过）:', div1);
  console.log('  第2行（未输入过）:', div2);

  console.log('\n' + '='.repeat(60));
  console.log('📋 对比分析:');
  console.log('='.repeat(60));

  // 对比所有可能的差异
  var properties = [
    'innerText',
    'innerHTML',
    'textContent',
    'contentEditable',
    'className',
    'id',
    'dataset',
    'attributes',
    'childNodes',
    'tabIndex',
    'spellcheck',
    'draggable'
  ];

  properties.forEach(function(prop) {
    var val1 = div1[prop];
    var val2 = div2[prop];

    console.log('\n' + prop + ':');
    console.log('  手动输入过:', val1);
    console.log('  未输入过:', val2);
    console.log('  是否相同:', JSON.stringify(val1) === JSON.stringify(val2));
  });

  // 对比所有 HTML 属性
  console.log('\n' + '='.repeat(60));
  console.log('📋 HTML 属性对比:');
  console.log('='.repeat(60));

  var attrs1 = Array.from(div1.attributes || []);
  var attrs2 = Array.from(div2.attributes || []);

  console.log('\n手动输入过的属性:', attrs1.length);
  attrs1.forEach(function(attr) {
    console.log('  ' + attr.name + ':', attr.value);
  });

  console.log('\n未输入过的属性:', attrs2.length);
  attrs2.forEach(function(attr) {
    console.log('  ' + attr.name + ':', attr.value);
  });

  // 对比 React Fiber
  console.log('\n' + '='.repeat(60));
  console.log('📋 React Fiber 对比:');
  console.log('='.repeat(60));

  var reactKey1 = Object.keys(div1).find(function(k) {
    return k.startsWith('__reactFiber') || k.startsWith('__reactInternal');
  });

  var reactKey2 = Object.keys(div2).find(function(k) {
    return k.startsWith('__reactFiber') || k.startsWith('__reactInternal');
  });

  if (reactKey1 && reactKey2) {
    var fiber1 = div1[reactKey1];
    var fiber2 = div2[reactKey2];

    console.log('\n手动输入过的 Fiber:');
    console.log('  memoizedProps:', fiber1.memoizedProps);
    console.log('  memoizedState:', fiber1.memoizedState);
    console.log('  pendingProps:', fiber1.pendingProps);

    console.log('\n未输入过的 Fiber:');
    console.log('  memoizedProps:', fiber2.memoizedProps);
    console.log('  memoizedState:', fiber2.memoizedState);
    console.log('  pendingProps:', fiber2.pendingProps);

    // 深度对比 memoizedProps
    console.log('\n🔍 memoizedProps 差异:');
    var props1 = fiber1.memoizedProps || {};
    var props2 = fiber2.memoizedProps || {};
    var allKeys = new Set([...Object.keys(props1), ...Object.keys(props2)]);

    allKeys.forEach(function(key) {
      if (JSON.stringify(props1[key]) !== JSON.stringify(props2[key])) {
        console.log('  ⭐ ' + key + ':');
        console.log('    手动输入过:', props1[key]);
        console.log('    未输入过:', props2[key]);
      }
    });
  }

  console.log('\n' + '='.repeat(60));
  console.log('✅ 对比完成！请仔细查看差异');
  console.log('='.repeat(60));

})();

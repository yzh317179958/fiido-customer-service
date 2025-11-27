/**
 * 诊断 v2：对比最后两行的 React 状态
 * 倒数第2行 = 手动输入
 * 最后1行 = 脚本填充
 */

(function() {
  console.clear();
  console.log('🔍 React Fiber 状态对比诊断 v2\n');

  var rows = document.querySelectorAll('tr.semi-table-row');

  if (rows.length < 2) {
    console.error('❌ 至少需要2行数据进行对比');
    return;
  }

  console.log('✅ 找到 ' + rows.length + ' 行数据\n');

  // 只分析最后两行
  var manualRow = rows[rows.length - 2];  // 倒数第2行（手动输入）
  var scriptRow = rows[rows.length - 1];  // 最后1行（脚本填充）

  function analyzeRow(row, label) {
    console.log('='.repeat(60));
    console.log('📋 ' + label);
    console.log('='.repeat(60));

    try {
      var cells = row.querySelectorAll('td.semi-table-row-cell');

      if (cells.length < 2) {
        console.log('  ⚠️  单元格不足');
        return null;
      }

      var questionCell = cells[0];
      var questionDiv = questionCell.querySelector('div.text-content');

      if (!questionDiv) {
        console.log('  ⚠️  找不到输入框');
        return null;
      }

      // 显示 DOM 内容
      console.log('\n📄 DOM 内容:');
      console.log('  问题 (innerText):', questionDiv.innerText);
      console.log('  问题 childNodes:', questionDiv.childNodes.length);

      // 查找 React Fiber
      var reactKey = Object.keys(questionDiv).find(function(k) {
        return k.startsWith('__reactFiber') || k.startsWith('__reactInternal');
      });

      if (!reactKey) {
        console.log('\n  ⚠️  未找到 React Fiber');
        return null;
      }

      console.log('\n🔧 React Fiber 分析:');

      var fiber = questionDiv[reactKey];
      var result = {
        hasValue: false,
        value: null,
        fiberDepth: null
      };

      // 遍历 Fiber 树找到有 value 的节点
      var currentFiber = fiber;
      var depth = 0;
      var maxDepth = 15;

      while (currentFiber && depth < maxDepth) {
        try {
          if (currentFiber.memoizedProps && currentFiber.memoizedProps.value !== undefined) {
            console.log('  ✅ 找到 value (层级 ' + depth + '):');
            console.log('    type:', typeof currentFiber.type === 'function' ? 'function' : currentFiber.type);
            console.log('    tag:', currentFiber.tag);
            console.log('    ⭐ value:', currentFiber.memoizedProps.value);

            result.hasValue = true;
            result.value = currentFiber.memoizedProps.value;
            result.fiberDepth = depth;
            result.fiber = currentFiber;

            break;
          }

          currentFiber = currentFiber.return;
          depth++;
        } catch (e) {
          console.error('  ❌ 遍历 Fiber 出错 (层级 ' + depth + '):', e.message);
          break;
        }
      }

      if (!result.hasValue) {
        console.log('  ❌ 未找到 value 属性（遍历了 ' + depth + ' 层）');
      }

      console.log('\n');
      return result;

    } catch (e) {
      console.error('❌ 分析出错:', e.message);
      return null;
    }
  }

  // 分析两行
  var manualResult = analyzeRow(manualRow, '倒数第2行（手动输入）');
  var scriptResult = analyzeRow(scriptRow, '最后1行（脚本填充）');

  // 对比结果
  console.log('='.repeat(60));
  console.log('📊 对比结果:');
  console.log('='.repeat(60));

  if (manualResult && scriptResult) {
    console.log('\n手动输入:');
    console.log('  有 value?', manualResult.hasValue);
    console.log('  value 值:', manualResult.value);
    console.log('  Fiber 层级:', manualResult.fiberDepth);

    console.log('\n脚本填充:');
    console.log('  有 value?', scriptResult.hasValue);
    console.log('  value 值:', scriptResult.value);
    console.log('  Fiber 层级:', scriptResult.fiberDepth);

    console.log('\n🔍 结论:');
    if (manualResult.hasValue && !scriptResult.hasValue) {
      console.log('  ❌ 问题确认：脚本填充的数据没有保存到 React 状态中！');
      console.log('  💡 解决方案：需要直接修改 React Fiber 的 value 属性');
      console.log('  📝 请测试 test_v14.js');
    } else if (manualResult.hasValue && scriptResult.hasValue) {
      console.log('  ✅ 两者都有 value，但可能值不正确');
      console.log('  💡 检查 value 值是否匹配 innerText');
    } else {
      console.log('  ⚠️  情况特殊，需要进一步分析');
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('✅ 诊断完成');
  console.log('='.repeat(60));

})();

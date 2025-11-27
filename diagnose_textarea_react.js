/**
 * 诊断：查看弹窗 textarea 的 React Fiber 状态
 */

(function() {
  console.clear();
  console.log('🔍 诊断弹窗 textarea 的 React 状态\n');
  console.log('⚠️  请先手动打开编辑弹窗，然后运行此脚本\n');

  // 查找弹窗
  var allModals = document.querySelectorAll('.semi-modal');
  var modal = null;

  for (var i = 0; i < allModals.length; i++) {
    var m = allModals[i];
    var textareas = m.querySelectorAll('textarea.semi-input-textarea');

    if (textareas.length >= 2) {
      modal = m;
      break;
    }
  }

  if (!modal) {
    console.error('❌ 找不到包含 textarea 的弹窗');
    console.log('请先手动打开编辑弹窗');
    return;
  }

  console.log('✅ 找到弹窗');

  var textareas = modal.querySelectorAll('textarea.semi-input-textarea');
  var textarea = textareas[0];  // 第一个 textarea

  console.log('✅ 找到第一个 textarea\n');

  // 查找 React Fiber
  var reactKey = Object.keys(textarea).find(function(k) {
    return k.startsWith('__reactFiber') || k.startsWith('__reactInternal');
  });

  if (!reactKey) {
    console.error('❌ 未找到 React Fiber');
    return;
  }

  console.log('✅ 找到 React Fiber\n');

  var fiber = textarea[reactKey];

  // 遍历 Fiber 树
  console.log('🔧 遍历 React Fiber 树:\n');

  var currentFiber = fiber;
  var depth = 0;
  var maxDepth = 15;

  while (currentFiber && depth < maxDepth) {
    console.log('层级 ' + depth + ':');
    console.log('  type:', typeof currentFiber.type === 'function' ? 'function' : currentFiber.type);
    console.log('  tag:', currentFiber.tag);

    if (currentFiber.memoizedProps) {
      var props = currentFiber.memoizedProps;

      // 显示重要的 props
      if (props.value !== undefined) {
        console.log('  ⭐ value:', props.value);
      }
      if (props.defaultValue !== undefined) {
        console.log('  ⭐ defaultValue:', props.defaultValue);
      }
      if (props.onChange) {
        console.log('  ⭐ onChange: 存在');
      }
      if (props.onInput) {
        console.log('  ⭐ onInput: 存在');
      }
    }

    console.log('');
    currentFiber = currentFiber.return;
    depth++;
  }

  console.log('='.repeat(60));
  console.log('🧪 测试填充:\n');

  // 测试1: 直接修改 value
  console.log('测试1: 设置 textarea.value = "测试内容"');
  textarea.value = '测试内容';
  console.log('  DOM value:', textarea.value);

  // 触发事件
  textarea.dispatchEvent(new Event('input', { bubbles: true }));
  textarea.dispatchEvent(new Event('change', { bubbles: true }));

  // 检查 React Fiber 的 value
  setTimeout(function() {
    var fiber = textarea[reactKey];
    var currentFiber = fiber;
    var depth = 0;

    console.log('\n触发事件后，检查 React Fiber:');

    while (currentFiber && depth < 15) {
      if (currentFiber.memoizedProps && currentFiber.memoizedProps.value !== undefined) {
        console.log('  层级 ' + depth + ' 的 value:', currentFiber.memoizedProps.value);
        break;
      }
      currentFiber = currentFiber.return;
      depth++;
    }

    console.log('\n' + '='.repeat(60));
    console.log('💡 如果 React Fiber 的 value 仍然是空的，');
    console.log('   说明需要调用 onChange 回调来更新 React 状态');
    console.log('='.repeat(60));

  }, 500);

})();

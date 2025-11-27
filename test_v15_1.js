/**
 * v15.1: 改进版 - 精确定位编辑按钮和弹窗输入框
 */

(function() {
  console.clear();
  console.log('🎯 v15.1: 通过编辑弹窗填充数据（改进版）\n');

  var testQuestion = 'v15测试问题';
  var testAnswer = 'v15测试答案';

  // 步骤1: 点击 Add value
  var addButton = document.querySelector('button.semi-button-primary');

  if (!addButton) {
    console.error('❌ 找不到 Add value 按钮');
    return;
  }

  console.log('✅ 找到 Add value 按钮');
  console.log('🚀 步骤1: 点击 Add value...');

  addButton.click();

  // 步骤2: 等待新行生成，然后点击编辑按钮
  setTimeout(function() {
    console.log('🚀 步骤2: 查找编辑按钮...');

    var rows = document.querySelectorAll('tr.semi-table-row');

    if (rows.length === 0) {
      console.error('❌ 找不到表格行');
      return;
    }

    var lastRow = rows[rows.length - 1];

    // 查找第3个单元格中的所有按钮
    var cells = lastRow.querySelectorAll('td.semi-table-row-cell');

    if (cells.length < 3) {
      console.error('❌ 单元格不足，找到 ' + cells.length + ' 个单元格');
      return;
    }

    var operationCell = cells[2];  // 第3个单元格

    console.log('✅ 找到操作列单元格');

    // 获取该单元格内的所有按钮
    var buttons = operationCell.querySelectorAll('button');

    console.log('找到 ' + buttons.length + ' 个按钮');

    // 列出所有按钮
    for (var i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      var btnText = btn.textContent.trim();
      console.log('  按钮 ' + i + ':', btnText || '(无文本，可能是图标按钮)');
    }

    // 精确选择编辑按钮（通过 SVG icon class）
    var editButton = null;

    for (var i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      var svg = btn.querySelector('svg');

      if (svg) {
        var svgClass = svg.className.baseVal || svg.className;
        console.log('  按钮 ' + i + ' SVG class:', svgClass);

        // 查找包含 "edit" 的 SVG（编辑图标）
        if (svgClass.includes('coz_edit')) {
          editButton = btn;
          console.log('    → 这是编辑按钮！');
          break;
        }
      }
    }

    if (!editButton && buttons.length >= 1) {
      // 备选：使用第一个按钮
      editButton = buttons[0];
      console.log('\n⚠️  未找到 coz_edit 图标，使用第一个按钮');
    }

    if (!editButton) {
      console.error('❌ 找不到编辑按钮');
      return;
    }

    console.log('✅ 找到编辑按钮');
    console.log('🚀 步骤3: 点击编辑按钮...');

    editButton.click();

    // 步骤3: 等待弹窗出现，填充数据
    setTimeout(function() {
      console.log('🚀 步骤4: 查找弹窗和输入框...');

      // 查找所有弹窗（可能有多个）
      var allModals = document.querySelectorAll('.semi-modal');
      console.log('找到 ' + allModals.length + ' 个弹窗');

      // 遍历查找包含 textarea 的弹窗（正确的弹窗）
      var modal = null;

      for (var i = 0; i < allModals.length; i++) {
        var m = allModals[i];
        var textareas = m.querySelectorAll('textarea.semi-input-textarea');

        console.log('  弹窗 ' + i + ' 中的 textarea 数量:', textareas.length);

        if (textareas.length >= 2) {
          modal = m;
          console.log('    → 这是正确的弹窗！');
          break;
        }
      }

      if (!modal) {
        console.error('❌ 找不到包含 textarea 的弹窗');
        console.log('所有弹窗:', allModals);
        return;
      }

      console.log('✅ 找到正确的弹窗');

      // 尝试多种方式查找输入框
      console.log('\n🔍 查找输入框...');

      // 优先查找 textarea.semi-input-textarea（正确的弹窗使用这个）
      var textareas = modal.querySelectorAll('textarea.semi-input-textarea');
      console.log('  textarea.semi-input-textarea:', textareas.length);

      // 备选方案
      var inputs = modal.querySelectorAll('input[type="text"]');
      console.log('  input[type="text"]:', inputs.length);

      var editableDivs = modal.querySelectorAll('div[contenteditable="true"]');
      console.log('  contenteditable div:', editableDivs.length);

      // 选择合适的输入框
      var inputFields = null;

      if (textareas.length >= 2) {
        inputFields = textareas;
        console.log('\n✅ 使用 textarea.semi-input-textarea');
      } else if (inputs.length >= 2) {
        inputFields = inputs;
        console.log('\n✅ 使用 input 元素');
      } else if (editableDivs.length >= 2) {
        inputFields = editableDivs;
        console.log('\n✅ 使用 contenteditable div');
      } else {
        console.error('\n❌ 找不到合适的输入框');
        console.log('\n请手动检查弹窗结构:');
        console.log(modal);
        return;
      }

      if (inputFields.length < 2) {
        console.error('❌ 输入框不足（需要2个，找到 ' + inputFields.length + ' 个）');
        return;
      }

      var questionInput = inputFields[0];
      var answerInput = inputFields[1];

      console.log('✅ 找到输入框');
      console.log('  问题框:', questionInput);
      console.log('  答案框:', answerInput);

      console.log('\n🚀 步骤5: 填充数据...');

      // 填充函数（支持多种输入框类型）
      function fillInput(element, text, label) {
        console.log('  填充 ' + label + ':', text);

        // 判断元素类型
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
          // 标准输入框
          element.value = text;
          element.dispatchEvent(new Event('input', { bubbles: true }));
          element.dispatchEvent(new Event('change', { bubbles: true }));
        } else if (element.contentEditable === 'true' || element.classList.contains('text-content')) {
          // contentEditable div
          element.innerText = text;
          element.dispatchEvent(new Event('input', { bubbles: true }));
          element.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
          console.warn('    ⚠️  未知的输入框类型');
        }

        console.log('    ✅ 填充完成');
      }

      // 填充数据
      fillInput(questionInput, testQuestion, '问题框');
      fillInput(answerInput, testAnswer, '答案框');

      console.log('\n' + '='.repeat(60));
      console.log('✅ 数据填充完成！');
      console.log('='.repeat(60));
      console.log('🔍 请检查:');
      console.log('  1. 弹窗中是否显示了数据？');
      console.log('  2. ⭐⭐⭐ 弹窗的 Confirm 按钮是否可点击？');
      console.log('  3. 如果可以，请手动点击 Confirm 按钮关闭弹窗');
      console.log('='.repeat(60));

    }, 1200); // 增加等待时间到1.2秒，确保弹窗完全加载

  }, 800); // 等待新行生成

  console.log('⏳ 开始执行...');

})();

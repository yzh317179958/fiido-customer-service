/**
 * v16.0: 完整的自动化流程（测试版 - 2行数据）
 *
 * 流程：
 * 1. 点击 Add value
 * 2. 点击编辑按钮
 * 3. 填充数据
 * 4. 点击 Save
 * 5. 重复
 */

(function() {
  console.clear();
  console.log('🎯 v16.0: 完整自动化流程（测试版）\n');

  // 测试数据（2行）
  var fillData = [
    { question: 'v16测试问题1', answer: 'v16测试答案1' },
    { question: 'v16测试问题2', answer: 'v16测试答案2' }
  ];

  var currentIndex = 0;

  // 查找 Add value 按钮
  var addButton = document.querySelector('button.semi-button-primary');

  if (!addButton) {
    console.error('❌ 找不到 Add value 按钮');
    return;
  }

  console.log('✅ 找到 Add value 按钮');
  console.log('📊 待填充数据: ' + fillData.length + ' 行\n');

  // 处理一行数据的完整流程
  function processRow() {
    if (currentIndex >= fillData.length) {
      console.log('\n' + '='.repeat(60));
      console.log('✅ 全部完成！共填充 ' + fillData.length + ' 行');
      console.log('='.repeat(60));
      console.log('\n🔍 请检查:');
      console.log('  1. 表格中是否显示所有数据？');
      console.log('  2. ⭐⭐⭐ 主 Confirm 按钮是否可点击？');
      console.log('  3. 如果可以，请手动点击主 Confirm 提交');
      console.log('='.repeat(60));
      return;
    }

    var data = fillData[currentIndex];
    var rowNumber = currentIndex + 1;

    console.log('='.repeat(60));
    console.log('📝 处理第 ' + rowNumber + '/' + fillData.length + ' 行');
    console.log('='.repeat(60));

    // 步骤1: 点击 Add value
    console.log('🚀 步骤1: 点击 Add value...');
    addButton.click();

    // 步骤2: 等待新行生成，点击编辑按钮
    setTimeout(function() {
      console.log('🚀 步骤2: 查找并点击编辑按钮...');

      var rows = document.querySelectorAll('tr.semi-table-row');
      var lastRow = rows[rows.length - 1];
      var cells = lastRow.querySelectorAll('td.semi-table-row-cell');

      if (cells.length < 3) {
        console.error('❌ 单元格不足');
        return;
      }

      var operationCell = cells[2];
      var buttons = operationCell.querySelectorAll('button');

      // 查找编辑按钮（coz_edit 图标）
      var editButton = null;

      for (var i = 0; i < buttons.length; i++) {
        var btn = buttons[i];
        var svg = btn.querySelector('svg');

        if (svg) {
          var svgClass = svg.className.baseVal || svg.className;

          if (svgClass.includes('coz_edit')) {
            editButton = btn;
            console.log('  ✅ 找到编辑按钮');
            break;
          }
        }
      }

      if (!editButton) {
        console.error('❌ 找不到编辑按钮');
        return;
      }

      editButton.click();

      // 步骤3: 等待弹窗出现，填充数据
      setTimeout(function() {
        console.log('🚀 步骤3: 填充数据...');

        // 查找包含 textarea 的弹窗
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
          console.error('❌ 找不到正确的弹窗');
          return;
        }

        console.log('  ✅ 找到弹窗');

        // 获取输入框
        var textareas = modal.querySelectorAll('textarea.semi-input-textarea');

        if (textareas.length < 2) {
          console.error('❌ 输入框不足');
          return;
        }

        var questionInput = textareas[0];
        var answerInput = textareas[1];

        // 填充问题框
        console.log('  📝 填充问题框...');
        questionInput.focus();
        questionInput.value = data.question;
        questionInput.dispatchEvent(new Event('input', { bubbles: true }));
        questionInput.dispatchEvent(new Event('change', { bubbles: true }));
        questionInput.blur();
        console.log('  ✅ 问题已填充:', data.question);

        // 等待一下再填充答案框
        setTimeout(function() {
          console.log('  📝 填充答案框...');
          answerInput.focus();
          answerInput.value = data.answer;
          answerInput.dispatchEvent(new Event('input', { bubbles: true }));
          answerInput.dispatchEvent(new Event('change', { bubbles: true }));
          answerInput.blur();
          console.log('  ✅ 答案已填充:', data.answer);

          // 步骤4: 等待 React 更新状态，再点击 Save
          setTimeout(function() {
            console.log('🚀 步骤4: 查找并点击 Save 按钮...');

          // 查找弹窗中的按钮
          var modalButtons = modal.querySelectorAll('button');
          var saveButton = null;

          for (var i = 0; i < modalButtons.length; i++) {
            var btn = modalButtons[i];
            var btnText = btn.textContent.trim().toLowerCase();

            // 查找 Save 或 Confirm 按钮
            if (btnText === 'save' || btnText === 'confirm' ||
                btnText === '保存' || btnText === '确认') {
              saveButton = btn;
              break;
            }
          }

          if (!saveButton) {
            console.error('❌ 找不到 Save 按钮');
            console.log('弹窗中的所有按钮:');
            for (var i = 0; i < modalButtons.length; i++) {
              console.log('  按钮 ' + i + ':', modalButtons[i].textContent.trim());
            }
            return;
          }

          console.log('  ✅ 找到 Save 按钮');
          saveButton.click();
          console.log('  ✅ 已点击 Save');

          // 步骤5: 等待弹窗关闭，处理下一行
          setTimeout(function() {
            console.log('✅ 第 ' + rowNumber + ' 行处理完成\n');

            currentIndex++;
            processRow();  // 处理下一行

          }, 800);  // 等待弹窗关闭

        }, 500);  // 填充后等待，再点击 Save

      }, 1200);  // 等待弹窗打开

    }, 800);  // 等待新行生成
  }

  // 开始执行
  setTimeout(function() {
    console.log('🚀 开始自动填充...\n');
    processRow();
  }, 1000);

  console.log('⏳ 1秒后开始执行...');
  console.log('⏱️  预计耗时: ' + (fillData.length * 3.5) + ' 秒\n');

})();

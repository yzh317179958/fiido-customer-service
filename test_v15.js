/**
 * v15.0: 通过编辑弹窗填充数据
 *
 * 策略：
 * 1. 点击 Add value 添加空行
 * 2. 点击该行的编辑按钮
 * 3. 在弹窗的 Field value 输入框中填值
 * 4. 点击弹窗的 Confirm 按钮
 */

(function() {
  console.clear();
  console.log('🎯 v15.0: 通过编辑弹窗填充数据\n');

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

    // 查找第3个单元格（第1列=问题，第2列=答案，第3列=操作按钮）
    var cells = lastRow.querySelectorAll('td.semi-table-row-cell');

    if (cells.length < 3) {
      console.error('❌ 单元格不足，找到 ' + cells.length + ' 个单元格');
      console.log('需要至少3个单元格（问题、答案、操作）');
      return;
    }

    var operationCell = cells[2];  // 第3个单元格（索引2）

    console.log('✅ 找到操作列单元格');

    // 在操作列中查找编辑按钮
    var editButton = operationCell.querySelector('button') ||
                     operationCell.querySelector('svg')?.closest('button') ||
                     operationCell.querySelector('[role="button"]');

    if (!editButton) {
      console.error('❌ 找不到编辑按钮');
      console.log('操作列单元格:', operationCell);
      console.log('该单元格内的按钮:', operationCell.querySelectorAll('button'));
      console.log('该单元格内的 SVG:', operationCell.querySelectorAll('svg'));
      return;
    }

    console.log('✅ 找到编辑按钮');
    console.log('🚀 步骤3: 点击编辑按钮...');

    editButton.click();

    // 步骤3: 等待弹窗出现，填充数据
    setTimeout(function() {
      console.log('🚀 步骤4: 查找弹窗输入框...');

      // 查找弹窗（可能的选择器）
      var modal = document.querySelector('.semi-modal') ||
                  document.querySelector('[role="dialog"]') ||
                  document.querySelector('.semi-portal');

      if (!modal) {
        console.error('❌ 找不到弹窗');
        console.log('请检查弹窗是否已打开');
        return;
      }

      console.log('✅ 找到弹窗:', modal);

      // 查找 Field value 输入框
      // 根据你的截图，应该有两个输入框（Index String 和 String）
      var inputs = modal.querySelectorAll('input[type="text"]') ||
                   modal.querySelectorAll('textarea') ||
                   modal.querySelectorAll('.semi-input');

      console.log('找到的输入框数量:', inputs.length);

      if (inputs.length < 2) {
        console.error('❌ 输入框不足（需要2个）');
        console.log('请检查输入框选择器');
        console.log('弹窗内所有 input:', modal.querySelectorAll('input'));
        console.log('弹窗内所有 textarea:', modal.querySelectorAll('textarea'));
        return;
      }

      // 第1个输入框 = Index String (问题)
      // 第2个输入框 = String (答案)
      var questionInput = inputs[0];
      var answerInput = inputs[1];

      console.log('✅ 找到输入框');
      console.log('  问题框:', questionInput);
      console.log('  答案框:', answerInput);

      console.log('🚀 步骤5: 填充数据...');

      // 填充问题
      questionInput.value = testQuestion;
      questionInput.dispatchEvent(new Event('input', { bubbles: true }));
      questionInput.dispatchEvent(new Event('change', { bubbles: true }));
      console.log('  ✅ 问题已填充:', testQuestion);

      // 填充答案
      answerInput.value = testAnswer;
      answerInput.dispatchEvent(new Event('input', { bubbles: true }));
      answerInput.dispatchEvent(new Event('change', { bubbles: true }));
      console.log('  ✅ 答案已填充:', testAnswer);

      console.log('\n' + '='.repeat(60));
      console.log('✅ 数据填充完成！');
      console.log('='.repeat(60));
      console.log('🔍 请检查:');
      console.log('  1. 弹窗中是否显示了数据？');
      console.log('  2. ⭐⭐⭐ 弹窗的 Confirm 按钮是否可点击？');
      console.log('  3. 如果可以，请手动点击 Confirm 按钮关闭弹窗');
      console.log('='.repeat(60));

    }, 800); // 等待弹窗打开

  }, 800); // 等待新行生成

  console.log('⏳ 开始执行...');

})();

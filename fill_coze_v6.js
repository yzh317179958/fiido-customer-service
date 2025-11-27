/**
 * Coze知识库自动填充脚本 v6.0
 * 修复：通过点击激活编辑模式后填充数据
 */

(function() {
  var fillData = [
    ["测试问题1", "测试答案1"],
    ["测试问题2", "测试答案2"]
  ];

  console.clear();
  console.log('🚀 Coze知识库自动填充工具 v6.0');
  console.log('='.repeat(60));
  console.log('📊 共 ' + fillData.length + ' 行数据待填充');
  console.log('='.repeat(60));

  var successCount = 0;
  var failCount = 0;
  var currentIndex = 0;

  function fillNextRow() {
    if (currentIndex >= fillData.length) {
      console.log('\n' + '='.repeat(60));
      console.log('🎉 填充任务完成！');
      console.log('='.repeat(60));
      console.log('✅ 成功: ' + successCount + ' 行');
      console.log('❌ 失败: ' + failCount + ' 行');
      console.log('📊 总计: ' + fillData.length + ' 行');
      console.log('\n⚠️  请手动检查数据后点击"Confirm"按钮提交');
      console.log('='.repeat(60));
      return;
    }

    var question = fillData[currentIndex][0];
    var answer = fillData[currentIndex][1];
    var rowNum = currentIndex + 1;

    console.log('\n[' + rowNum + '/' + fillData.length + '] 正在处理...');
    console.log('  问题: ' + question.substring(0, 50) + '...');

    try {
      // 步骤1: 点击"Add value"按钮
      var addButton = null;
      var allButtons = document.querySelectorAll('button');

      for (var i = 0; i < allButtons.length; i++) {
        var btn = allButtons[i];
        var btnText = btn.textContent || '';
        if (btnText.indexOf('Add value') !== -1 ||
            btnText.indexOf('add') !== -1 ||
            btnText.indexOf('添加') !== -1) {
          addButton = btn;
          break;
        }
      }

      if (!addButton) {
        console.error('  ❌ 找不到"Add value"按钮');
        failCount++;
        currentIndex++;
        setTimeout(fillNextRow, 300);
        return;
      }

      addButton.click();
      console.log('  ✓ 已点击"Add value"按钮');

      // 步骤2: 等待新行加载，然后查找并点击输入区域
      setTimeout(function() {
        try {
          // 查找所有表格行
          var rows = document.querySelectorAll('tr.semi-table-row');
          console.log('  🔍 找到表格行数:', rows.length);

          if (rows.length === 0) {
            console.error('  ❌ 找不到表格行');
            failCount++;
            currentIndex++;
            setTimeout(fillNextRow, 500);
            return;
          }

          // 获取最后一行（刚添加的）
          var lastRow = rows[rows.length - 1];
          console.log('  ✓ 定位到最后一行');

          // 查找该行的所有单元格
          var cells = lastRow.querySelectorAll('td.semi-table-row-cell');
          console.log('  🔍 找到单元格数:', cells.length);

          if (cells.length < 2) {
            console.error('  ❌ 单元格数量不足');
            failCount++;
            currentIndex++;
            setTimeout(fillNextRow, 500);
            return;
          }

          // 第1个单元格：问题
          // 第2个单元格：答案
          var questionCell = cells[0];
          var answerCell = cells[1];

          // 查找单元格内的可编辑区域 div.text-content
          var questionDiv = questionCell.querySelector('div.text-content');
          var answerDiv = answerCell.querySelector('div.text-content');

          if (!questionDiv || !answerDiv) {
            console.error('  ❌ 找不到可编辑区域');
            console.log('    questionDiv:', questionDiv);
            console.log('    answerDiv:', answerDiv);
            failCount++;
            currentIndex++;
            setTimeout(fillNextRow, 500);
            return;
          }

          console.log('  ✓ 找到可编辑区域');

          // 步骤3: 点击激活编辑模式
          questionDiv.click();
          console.log('  ✓ 点击问题输入框');

          setTimeout(function() {
            try {
              // 填充问题
              questionDiv.focus();
              questionDiv.textContent = question;

              // 触发输入事件
              var inputEvent = new Event('input', { bubbles: true });
              var changeEvent = new Event('change', { bubbles: true });
              questionDiv.dispatchEvent(inputEvent);
              questionDiv.dispatchEvent(changeEvent);

              console.log('  ✓ 已填写问题');

              // 点击答案区域
              answerDiv.click();
              console.log('  ✓ 点击答案输入框');

              setTimeout(function() {
                // 填充答案
                answerDiv.focus();
                answerDiv.textContent = answer;
                answerDiv.dispatchEvent(inputEvent);
                answerDiv.dispatchEvent(changeEvent);

                console.log('  ✅ 数据填写完成');
                successCount++;

                currentIndex++;

                if (failCount >= 5) {
                  console.error('\n⚠️  连续失败过多，脚本已暂停');
                  return;
                }

                // 继续下一行
                setTimeout(fillNextRow, 500);

              }, 300); // 等待答案输入框激活

            } catch (error) {
              console.error('  ❌ 填写数据失败: ' + error.message);
              failCount++;
              currentIndex++;
              setTimeout(fillNextRow, 500);
            }
          }, 300); // 等待问题输入框激活

        } catch (error) {
          console.error('  ❌ 处理行失败: ' + error.message);
          failCount++;
          currentIndex++;
          setTimeout(fillNextRow, 500);
        }
      }, 1000); // 等待新行加载（增加到1秒）

    } catch (error) {
      console.error('  ❌ 处理失败: ' + error.message);
      failCount++;
      currentIndex++;
      setTimeout(fillNextRow, 500);
    }
  }

  fillNextRow();
})();

/**
 * 手动测试脚本 - 找到最后一行并尝试多种填充方式
 * 请先手动点击一次 "Add value"，然后运行此脚本
 */

(function() {
  console.clear();
  console.log('🧪 开始测试填充方式...\n');

  // 1. 找到最后一行
  var rows = document.querySelectorAll('tr.semi-table-row');
  if (rows.length === 0) {
    console.error('❌ 找不到表格行');
    return;
  }

  var lastRow = rows[rows.length - 1];
  console.log('✅ 找到最后一行:', lastRow);

  // 2. 找到单元格
  var cells = lastRow.querySelectorAll('td.semi-table-row-cell');
  console.log('✅ 找到单元格数:', cells.length);

  if (cells.length < 2) {
    console.error('❌ 单元格不足');
    return;
  }

  var questionCell = cells[0];
  var answerCell = cells[1];

  // 3. 找到可编辑区域
  var questionDiv = questionCell.querySelector('div.text-content');
  var answerDiv = answerCell.querySelector('div.text-content');

  console.log('✅ 问题输入框:', questionDiv);
  console.log('✅ 答案输入框:', answerDiv);

  console.log('\n📝 当前内容:');
  console.log('  问题 textContent:', questionDiv.textContent);
  console.log('  问题 innerHTML:', questionDiv.innerHTML);
  console.log('  答案 textContent:', answerDiv.textContent);
  console.log('  答案 innerHTML:', answerDiv.innerHTML);

  // 4. 测试各种填充方式
  console.log('\n🧪 测试填充方式...');

  var testQuestion = '这是测试问题';
  var testAnswer = '这是测试答案';

  // 方式1: textContent
  console.log('\n方式1: 使用 textContent');
  questionDiv.textContent = testQuestion;
  console.log('  设置后 textContent:', questionDiv.textContent);
  console.log('  设置后 innerHTML:', questionDiv.innerHTML);

  // 方式2: innerHTML
  console.log('\n方式2: 使用 innerHTML');
  answerDiv.innerHTML = testAnswer;
  console.log('  设置后 textContent:', answerDiv.textContent);
  console.log('  设置后 innerHTML:', answerDiv.innerHTML);

  // 方式3: innerText
  console.log('\n方式3: 使用 innerText');
  questionDiv.innerText = testQuestion + ' (innerText)';
  console.log('  设置后 innerText:', questionDiv.innerText);

  // 方式4: 模拟键盘输入
  console.log('\n方式4: 触发事件');
  var events = ['focus', 'input', 'change', 'blur'];
  events.forEach(function(eventType) {
    var event = new Event(eventType, { bubbles: true, cancelable: true });
    questionDiv.dispatchEvent(event);
    console.log('  触发事件:', eventType);
  });

  // 方式5: 检查是否是 contenteditable
  console.log('\n方式5: 检查 contenteditable');
  console.log('  问题框 contentEditable:', questionDiv.contentEditable);
  console.log('  答案框 contentEditable:', answerDiv.contentEditable);

  // 尝试设置 contenteditable
  questionDiv.setAttribute('contenteditable', 'true');
  answerDiv.setAttribute('contenteditable', 'true');
  console.log('  设置后 contentEditable:', questionDiv.contentEditable);

  // 方式6: 使用 document.execCommand
  console.log('\n方式6: 使用 execCommand');
  questionDiv.focus();
  if (document.execCommand) {
    document.execCommand('selectAll', false, null);
    document.execCommand('insertText', false, testQuestion);
    console.log('  execCommand 执行完成');
  }

  console.log('\n✅ 测试完成！请查看页面是否有内容填充');
  console.log('⚠️  如果页面有内容显示，记录是哪种方式成功的');
})();

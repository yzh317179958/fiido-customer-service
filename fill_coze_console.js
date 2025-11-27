/**
 * Coze知识库自动填充脚本 - 浏览器控制台版本
 *
 * 使用方法:
 * 1. 打开Firefox浏览器控制台 (F12)
 * 2. 先运行步骤1的数据准备代码
 * 3. 然后运行步骤2的自动填充代码
 */

// ==================== 步骤1: 准备数据 ====================
// 将Excel数据复制粘贴到这里（跳过标题行）
const excelData = [
  ["C11pro车架是铝合金吗？整车的重量是多少？", "Fiido C11 Pro的车架采用高品质铝合金制造，这一材质在保证车架坚固耐用的同时，实现..."],
  ["C11pro刹车系统是机械碟刹还是液压碟刹？", "关于Fiido C11 Pro的刹车系统，它配备了性能更优的液压碟刹。\n这套刹车系统具备两..."],
  // ... 添加所有141行数据
];

console.log(`📊 数据准备完成，共 ${excelData.length} 行`);


// ==================== 步骤2: 自动填充 ====================
async function fillCozeData() {
  console.log('🚀 开始自动填充...');

  for (let i = 0; i < excelData.length; i++) {
    const [question, answer] = excelData[i];

    console.log(`[${i+1}/${excelData.length}] 填写: ${question.substring(0, 30)}...`);

    // 1. 点击"Add value"按钮
    const addButton = document.querySelector('button');
    if (addButton && addButton.textContent.includes('Add value')) {
      addButton.click();
      await new Promise(r => setTimeout(r, 300)); // 等待300ms
    }

    // 2. 查找输入框
    const inputs = document.querySelectorAll('input[type="text"], textarea');

    if (inputs.length >= 2) {
      // 最后两个输入框
      const questionInput = inputs[inputs.length - 2];
      const answerInput = inputs[inputs.length - 1];

      // 填充数据
      questionInput.value = question;
      questionInput.dispatchEvent(new Event('input', { bubbles: true }));

      answerInput.value = answer;
      answerInput.dispatchEvent(new Event('input', { bubbles: true }));

      console.log(`  ✅ 完成`);
    } else {
      console.error(`  ❌ 错误: 找不到输入框`);
      break;
    }

    // 短暂延迟
    await new Promise(r => setTimeout(r, 200));
  }

  console.log('🎉 所有数据填充完成！');
  console.log('⚠️  请手动检查并点击"Confirm"按钮');
}

// 运行填充
// fillCozeData();

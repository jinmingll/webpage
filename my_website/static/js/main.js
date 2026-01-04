// 情绪垃圾桶提交动画 + 异步提交数据
function submitTrash() {
    // 验证验证码
    const inputCode = document.getElementById('verify_code').value;
    const trueCode = document.getElementById('true_verify_code').innerText;
    if (inputCode !== trueCode) {
        alert('验证码错误～小行星没进轨道哦！');
        return;
    }

    // 获取提交内容
    const content = document.getElementById('trash_content').value;
    const trashImg = document.getElementById('trash_img'); // 图片上传DOM
    const isAnonymous = document.getElementById('anonymous').checked;
    if (!content) {
        alert('请输入要扔掉的“垃圾”～');
        return;
    }

    // 随机暖心回复列表
    const warmReplies = [
        "垃圾已经扔掉啦～✨ 坏心情也一起飞走了",
        "垃圾桶已收到你的烦恼，现在清空啦😘",
        "不开心的事都丢进黑洞啦，剩下的都是快乐～",
        "烦恼回收成功！奖励自己一个甜甜的微笑😊",
        "情绪垃圾已处理，今天也要元气满满哦💪"
    ];
    const randomReply = warmReplies[Math.floor(Math.random() * warmReplies.length)];

    // 动画元素
    const trashContent = document.getElementById('trash-content');
    const trashCan = document.getElementById('trash-can');
    
    // 设置内容
    trashContent.innerText = content;
    trashContent.style.display = 'block';

    // 移动动画
    let x = trashContent.offsetLeft;
    let y = trashContent.offsetTop;
    const targetX = trashCan.offsetLeft + trashCan.offsetWidth/2 - trashContent.offsetWidth/2;
    const targetY = trashCan.offsetTop - trashContent.offsetHeight;

    const timer = setInterval(() => {
        x += (targetX - x) / 10;
        y += (targetY - y) / 10;
        trashContent.style.left = x + 'px';
        trashContent.style.top = y + 'px';
        trashContent.style.opacity = parseFloat(trashContent.style.opacity || 1) - 0.05;
        trashContent.style.transform = `scale(${parseFloat(trashContent.style.transform?.replace('scale(', '') || 1) - 0.05})`;

        // 到达目标后停止
        if (Math.abs(x - targetX) < 5 && Math.abs(y - targetY) < 5) {
            clearInterval(timer);
            trashContent.style.display = 'none';
            // 垃圾桶晃动
            trashCan.style.transform = 'rotate(5deg)';
            setTimeout(() => {
                trashCan.style.transform = 'rotate(-5deg)';
                setTimeout(() => {
                    trashCan.style.transform = 'rotate(0)';
                    // 1. 异步提交数据（含图片）
                    submitTrashData(content, trashImg, isAnonymous, randomReply);
                    // 2. 重置表单
                    document.getElementById('trash_form').reset();
                }, 100);
            }, 100);
        }
    }, 30);
}

// 异步提交垃圾数据到后端（恢复图片上传）
function submitTrashData(content, imgFile, isAnonymous, reply) {
    // 创建FormData对象（支持文件上传）
    const formData = new FormData();
    formData.append('trash_content', content);
    formData.append('anonymous', isAnonymous); // 布尔值转字符串
    // 处理图片上传
    if (imgFile.files && imgFile.files.length > 0) {
        formData.append('trash_img', imgFile.files[0]);
    }

    // 发送AJAX请求
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/trash', true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            // 提交成功：弹窗提示 → 点击确定跳首页
            if (confirm(`${reply}\n\n点击“确定”返回首页～`)) {
                window.location.href = '/'; // 跳转到首页
            }
        } else {
            alert('提交失败啦😥，再试一次吧！');
        }
    };
    // 网络错误处理
    xhr.onerror = function() {
        alert('网络出错了～检查一下再试吧！');
    };
    xhr.send(formData);
}

// 页面加载完成后执行
window.onload = function() {
    const submitBtn = document.getElementById('submit_trash_btn');
    if (submitBtn) {
        submitBtn.onclick = submitTrash;
    }
};
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session
import json
import os
import uuid
from datetime import datetime

# 初始化Flask应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = 'dev_2026'  # 加密session（必须设置）
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # session有效期1小时

# 确保文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
for file in ['posts.json', 'trash.json', 'users.json']:
    if not os.path.exists(file):
        with open(file, 'w', encoding='utf-8') as f:
            json.dump([], f)

# ---------------------- 辅助函数 ----------------------
def load_json(file_path):
    """读取JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path, data):
    """保存到JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_current_user():
    """获取当前登录用户（从session）"""
    return session.get('username')

# ---------------------- 用户相关路由 ----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 校验用户名是否已存在
        users = load_json('users.json')
        for user in users:
            if user['username'] == username:
                return render_template('register.html', error='用户名已存在！')
        
        # 新增用户
        user_data = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': password,  # 注：作业级简化，未加密（实际项目需加密）
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        users.append(user_data)
        save_json('users.json', users)
        return redirect('/login')  # 注册成功跳登录
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 校验用户
        users = load_json('users.json')
        for user in users:
            if user['username'] == username and user['password'] == password:
                # 登录成功，写入session
                session['username'] = username
                session.permanent = True  # 持久化session
                return redirect('/')  # 跳首页
        
        return render_template('login.html', error='用户名或密码错误！')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """用户退出"""
    session.pop('username', None)  # 清除session
    return redirect('/login')

# ---------------------- 登录验证装饰器（简化版） ----------------------
def login_required(func):
    """装饰器：未登录则跳登录页"""
    def wrapper(*args, **kwargs):
        if not get_current_user():
            return redirect('/login')
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__  # 修复Flask路由命名问题
    return wrapper

# ---------------------- 核心业务路由（添加登录验证+用户绑定） ----------------------
@app.route('/')
@login_required  # 首页需登录
def index():
    """首页（仅显示当前用户的日志）"""
    current_user = get_current_user()
    posts = load_json('posts.json')
    # 过滤：仅显示当前用户的日志
    user_posts = [p for p in posts if p['username'] == current_user]
    user_posts.sort(key=lambda x: x['time'], reverse=True)
    
    # 彩蛋：特定日期祝福语
    today = datetime.now()
    egg = ""
    if today.month == 10 and today.day == 1:
        egg = "🎉 国庆节快乐～"
    return render_template('index.html', posts=user_posts, egg=egg, username=current_user)

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    """发布日志（绑定当前用户）"""
    current_user = get_current_user()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        tag = request.form.get('tag')
        img = request.files.get('img')
        video_url = request.form.get('video_url')

        # 处理图片
        img_url = ""
        if img and img.filename:
            filename = f"{uuid.uuid4()}_{img.filename.replace(' ', '_')}"
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_url = f"/static/uploads/{filename}"

        # 构造日志（绑定当前用户）
        post_data = {
            'id': str(uuid.uuid4()),
            'username': current_user,  # 关键：绑定用户
            'title': title,
            'content': content,
            'tag': tag,
            'img_url': img_url,
            'video_url': video_url,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'comments': []
        }

        # 保存
        posts = load_json('posts.json')
        posts.append(post_data)
        save_json('posts.json', posts)
        return redirect('/')
    
    return render_template('post.html', username=current_user)

@app.route('/add_comment/<post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    """添加留言（仅能给自己的日志加留言）"""
    current_user = get_current_user()
    name = request.form.get('name')
    comment = request.form.get('comment')
    
    # 校验：仅操作自己的日志
    posts = load_json('posts.json')
    for post in posts:
        if post['id'] == post_id and post['username'] == current_user:
            post['comments'].append({
                'id': str(uuid.uuid4()),
                'name': name,
                'content': comment,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            save_json('posts.json', posts)
            break
    return redirect('/')

@app.route('/trash', methods=['GET', 'POST'])
@login_required
def trash():
    """情绪垃圾桶（绑定当前用户）"""
    current_user = get_current_user()
    if request.method == 'POST':
        content = request.form.get('trash_content')
        img = request.files.get('trash_img')
        is_anonymous = request.form.get('anonymous') in ['True', 'true', True]

        # 处理图片
        img_url = ""
        if img and img.filename:
            filename = f"{uuid.uuid4()}_{img.filename.replace(' ', '_')}"
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_url = f"/static/uploads/{filename}"

        # 构造垃圾数据（绑定用户）
        trash_data = {
            'id': str(uuid.uuid4()),
            'username': current_user,  # 关键：绑定用户
            'uuid': str(uuid.uuid4()) if is_anonymous else 'non-anon',
            'content': content,
            'img_url': img_url,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 保存
        trashes = load_json('trash.json')
        trashes.append(trash_data)
        save_json('trash.json', trashes)
        return jsonify({'status': 'success', 'trash_uuid': trash_data['uuid']})

    verify_code = str(datetime.now().second % 10)
    return render_template('trash.html', verify_code=verify_code, username=current_user)

@app.route('/admin')
@login_required
def admin():
    """后台管理（仅显示当前用户的内容）"""
    current_user = get_current_user()
    # 过滤：仅显示自己的日志和垃圾桶数据
    posts = [p for p in load_json('posts.json') if p['username'] == current_user]
    trashes = [t for t in load_json('trash.json') if t['username'] == current_user]
    return render_template('admin.html', posts=posts, trashes=trashes, username=current_user)

@app.route('/delete/<type>/<item_id>')
@login_required
def delete(type, item_id):
    """删除内容（仅删除自己的）"""
    current_user = get_current_user()
    if type == 'post':
        posts = load_json('posts.json')
        # 过滤：仅保留非当前用户/非当前ID的日志
        new_posts = [p for p in posts if not (p['id'] == item_id and p['username'] == current_user)]
        save_json('posts.json', new_posts)
    elif type == 'trash':
        trashes = load_json('trash.json')
        new_trashes = [t for t in trashes if not (t['id'] == item_id and t['username'] == current_user)]
        save_json('trash.json', new_trashes)
    return redirect('/admin')

# 启动应用
if __name__ == '__main__':
    app.run(debug=True)
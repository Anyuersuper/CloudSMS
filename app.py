from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import hashlib
import os
import secrets
from datetime import datetime
import uuid
import time
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 设置时区
tz = pytz.timezone('Asia/Shanghai')

db = SQLAlchemy(app)

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 用户模型
class User(db.Model):
    __tablename__ = 'users'  # 明确指定表名
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    api_key = db.Column(db.String(64), unique=True, nullable=True)

    def check_password(self, password):
        return self.password == hash_password(password, self.salt)

# 短信模型
class Message(db.Model):
    __tablename__ = 'messages'  # 明确指定表名
    id = db.Column(db.String(64), primary_key=True)  # 使用字符串作为主键
    username = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# 初始化数据库
def init_db():
    with app.app_context():
        db.create_all()
        print("数据库表已创建")

# 调用初始化函数
init_db()

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def generate_api_key():
    return secrets.token_hex(32)

def generate_message_id():
    # 生成时间戳（毫秒级）
    timestamp = int(time.time() * 1000)
    # 生成UUID并只取前6位
    unique_id = str(uuid.uuid4()).replace('-', '')[:6]
    # 组合时间戳和UUID
    return f"{timestamp}_{unique_id}"




@app.route('/cloudsms/')
def index():
    if 'username' in session:
        return redirect(url_for('/cloudsms/dashboard'))
    return render_template('index.html')

@app.route('/cloudsms/dashboard')
@login_required
def dashboard():
    # 获取当前用户
    user = User.query.filter_by(username=session['username']).first()
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条
    
    # 获取用户的短信，按时间倒序排列
    messages = Message.query.filter_by(username=user.username)\
        .order_by(Message.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # 转换时间为北京时间
    for message in messages.items:
        if message.created_at.tzinfo is None:
            message.created_at = tz.localize(message.created_at)
        else:
            message.created_at = message.created_at.astimezone(tz)
    
    return render_template('dashboard.html', 
                         username=user.username,
                         api_key=user.api_key,
                         messages=messages)

@app.route('/cloudsms/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('register'))
            
        salt = secrets.token_hex(16)
        hashed_password = hash_password(password, salt)
        api_key = generate_api_key()  # 生成API密钥
        
        new_user = User(username=username, password=hashed_password, salt=salt, api_key=api_key)
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/cloudsms/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
            return render_template('index.html')
    
    return render_template('index.html')

@app.route('/cloudsms/logout')
def logout():
    session.pop('username', None)
    flash('您已成功退出登录', 'info')
    return redirect(url_for('index'))

# API接口
@app.route('/cloudsms/api/send', methods=['POST'])
def api_send():
    # 从URL参数获取API密钥
    api_key = request.args.get('X-API-Key')
    if not api_key:
        return jsonify({'error': '缺少API密钥'}), 401
    
    # 验证API密钥
    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': '无效的API密钥'}), 401
    
    # 获取短信内容
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': '缺少短信内容'}), 400
    
    # 检查内容长度
    if len(data['content']) > 500:  # 限制短信长度
        return jsonify({'error': '短信内容过长'}), 400
    
    # 检查请求频率
    recent_messages = Message.query.filter_by(username=user.username)\
        .order_by(Message.created_at.desc())\
        .limit(10)\
        .all()
    
    if recent_messages and len(recent_messages) >= 10:
        last_message_time = recent_messages[-1].created_at
        time_diff = datetime.now() - last_message_time
        if time_diff.total_seconds() < 60:  # 限制1分钟内最多10条
            return jsonify({'error': '发送频率过高，请稍后再试'}), 429
    
    # 创建新短信
    message_id = generate_message_id()
    new_message = Message(id=message_id, username=user.username, content=data['content'])
    db.session.add(new_message)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '短信发送成功',
        'message_id': message_id
    })

if __name__ == '__main__':
    app.run(debug=True) 
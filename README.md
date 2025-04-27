# ☁️📨 云短信平台

一个简单的短信发送和管理平台，支持用户注册、登录、发送短信和API调用。

---

## ✨ 功能特点

- 👤 用户注册和登录
- 📨 短信发送和管理
- 🔗 RESTful API接口
- 🎨 美观的现代化界面
- 🔒 安全的密码存储
- 🗝️ API密钥管理

---

## ⚙️ 安装说明

1. 安装依赖：

```bash
pip install flask flask-sqlalchemy pytz
```

2. 运行应用：

```bash
python app.py
```

---

## 🚀 使用说明

### 🖥️ 用户界面

1. 📝 注册账号
   - 访问注册页面
   - 输入用户名和密码
   - 系统会自动生成API密钥

2. 🔑 登录系统
   - 使用注册的账号登录
   - 登录后进入仪表盘

3. 📬 查看短信
   - 在仪表盘查看最新短信
   - 点击短信可查看完整内容
   - 支持分页浏览

### 🛠️ API使用

1. 发送短信
   - 请求地址：`/api/send?X-API-Key=你的API密钥`
   - 请求方法：POST
   - 请求体格式：
     ```json
     {
         "content": "短信内容"
     }
     ```

2. 注意事项
   - ✉️ 短信内容长度限制：500字符
   - ⏱️ 发送频率限制：1分钟内最多10条
   - 🗝️ API密钥请妥善保管，不要泄露

3. 示例代码
   ```python
   import requests
   
   url = "http://your-domain/api/send"
   params = {
       "X-API-Key": "your-api-key"
   }
   data = {
       "content": "这是一条测试短信"
   }
   
   response = requests.post(url, params=params, json=data)
   print(response.json())
   ```

---

## 🧩 技术栈

- 🐍 后端：Flask + SQLAlchemy
- 🗄️ 数据库：SQLite
- 💻 前端：Bootstrap 5
- 🛡️ 密码加密：SHA-256 + Salt

---

## 🛡️ 安全特性

- 🧂 密码加盐哈希存储
- 🗝️ API密钥验证
- ⏳ 请求频率限制
- 🗂️ 会话管理

---

## 🛠️ 开发说明

1. 🗃️ 数据库初始化
   - 应用启动时自动创建数据库表
   - 无需手动初始化

2. 🐞 调试模式
   - 开发时启用调试模式
   - 生产环境请关闭调试模式

---

## ⚠️ 注意事项

- ❗ 请勿在生产环境使用默认的SECRET_KEY
- 💾 定期备份数据库文件
- 🔐 建议使用HTTPS加密传输
- 🗝️ API密钥请妥善保管

---

## �� 许可证

MIT License 
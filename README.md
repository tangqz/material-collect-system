# 学生材料提交系统

这是一个基于Flask的学生材料提交系统，用于收集和管理学生提交的作业材料。

## 功能特性
- 学生身份验证
- 材料提交与覆盖
- 提交状态查看
- 管理员批量下载
- 文件格式验证

## 环境要求
- Python 3.8+
- Flask 2.0+
- Pandas
- python-dotenv

## 安装步骤

1. 克隆仓库：
   ```bash
   git clone https://github.com/tangqz/material-collect-system.git
   cd material-collect-system
   ```

2. 创建虚拟环境：
   ```bash
   python -m venv venv
   ```

3. 激活虚拟环境：
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

5. 配置环境变量：
   - 复制`.env.example`为`.env`
   - 编辑`.env`文件，设置以下变量：
     ```
     FLASK_SECRET_KEY=your-secret-key-here
     ADMIN_PASSWORD=your-admin-password-here
     ```

## 运行系统

1. 启动开发服务器：
   ```bash
   python app.py
   ```

2. 访问系统：
   - 学生提交页面：http://localhost:5000/submit
   - 状态查看页面：http://localhost:5000/status
   - 管理员页面：http://localhost:5000/admin

## 注意事项
1. 部署前请确保：
   - 已设置强密码
   - 已生成安全的FLASK_SECRET_KEY
   - 已配置正确的上传目录权限

2. 学生数据文件格式：
   - 文件路径：backend/config/students.csv
   - 格式要求：
     ```
     student_id,name
     1,学生1
     2,学生2
     ...
     ```

3. 系统默认使用SQLite数据库存储提交记录，生产环境建议使用更健壮的数据库系统。

## 许可证
MIT License

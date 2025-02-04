from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, IntegerField
from wtforms.validators import DataRequired, NumberRange, ValidationError
from werkzeug.utils import secure_filename
import re
import pandas as pd
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
app.config['UPLOAD_FOLDER'] = '/uploads'
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024  # 30MB

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 读取学生名单
try:
    students_df = pd.read_csv('backend/config/students.xlsx')
    students = students_df.to_dict('records')
except FileNotFoundError:
    raise Exception("Students configuration file not found at backend/config/students.xlsx")
except Exception as e:
    raise Exception(f"Error reading students file: {str(e)}")

class AdminForm(FlaskForm):
    password = PasswordField('管理员密码', validators=[DataRequired()])

class SubmitForm(FlaskForm):
    student_id = IntegerField('学号', validators=[
        DataRequired(),
        NumberRange(min=1, max=50, message="学号必须在1-50之间")
    ])
    name = StringField('姓名', validators=[DataRequired()])
    file = FileField('材料文件', validators=[DataRequired()])
    
    def validate_file(self, field):
        # 支持的压缩包格式
        allowed_extensions = {'zip', 'rar', '7z'}
        filename = field.data.filename.lower()
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise ValidationError('仅支持zip、rar、7z格式的压缩包')


def get_status():
    status_list = []
    for student in students:
        student_id = student['student_id']
        folder_name = f"{student_id}_{student['name']}"
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
        status = '已提交' if os.path.exists(folder_path) else '未提交'
        last_submit_time = None
        if status == '已提交':
            # Get latest file modification time
            files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
            if files:
                # 获取文件修改时间戳
                max_mtime = max(os.path.getmtime(f) for f in files)
                # 将时间戳转换为 datetime 对象（UTC）
                utc_time = datetime.utcfromtimestamp(max_mtime)
                # 调整为东8区时间
                last_submit_time = (utc_time + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        status_list.append({
            'student_id': student_id,
            'name': student['name'],
            'status': status,
            'last_submit_time': last_submit_time
        })
    return status_list

def validate_student(student_id, name):
    student = next((s for s in students if s['student_id'] == student_id), None)
    return student and student['name'] == name

def adjust_time_for_timezone(dt):
    """
    将时间的小时数加8，并处理进位（例如，超过24小时的情况）。
    """
    adjusted_dt = dt + timedelta(hours=8)
    return adjusted_dt

@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('submit'))

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    form = SubmitForm()
    if form.validate_on_submit():
        student_id = form.student_id.data
        name = form.name.data
        
        # 验证学号和姓名是否匹配
        if not validate_student(student_id, name):
            flash('学号和姓名不匹配', 'danger')
            return jsonify({'success': False, 'message': '学号和姓名不匹配'}), 400
            
        file = form.file.data
        # 使用时间戳重命名文件
        current_time = datetime.now()
        adjusted_time = adjust_time_for_timezone(current_time)  # 调整时区
        timestamp = adjusted_time.strftime('%Y%m%d_%H%M%S')
        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{timestamp}{ext}"
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        try:
            folder_name = f"{student_id}_{name}"
            target_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
            overwrite = False
            
            # 如果文件夹已存在，先删除旧文件
            if os.path.exists(target_folder):
                flash('检测到已有提交，将覆盖之前的文件。', 'warning')
                shutil.rmtree(target_folder)
                overwrite = True
                
            os.makedirs(target_folder, exist_ok=True)
            final_path = os.path.join(target_folder, filename)
            shutil.move(temp_path, final_path)
            flash('提交已完成。', 'success')
            return jsonify({
                'success': True,
                'message': '提交已完成',
                'overwrite': overwrite  # 返回是否覆盖的标志
            })
        except Exception as e:
            flash(f'文件处理失败: {str(e)}', 'danger')
            return jsonify({
                'success': False,
                'message': f'文件处理失败: {str(e)}'
            }), 500
        finally:
            # 确保文件存在才删除
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    # 如果是 GET 请求或表单验证失败，渲染页面
    return render_template('submit.html', form=form)

@app.route('/status')
def status():
    status_list = get_status()
    return render_template('status.html', status_list=status_list)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    form = AdminForm()
    if form.validate_on_submit():
        if form.password.data.strip() == "admin123":
            return render_template('admin.html', form=form, admin_logged_in=True)
        else:
            flash('密码错误', 'danger')
    return render_template('admin.html', form=form, admin_logged_in=False)

@app.route('/download_all')
def download_all():
    # 检查session中的管理员状态
    if not request.args.get('admin') == 'true':
        return redirect(url_for('admin_login'))
    
    # 设置下载链接有效期
    return redirect(url_for('_download_all', timestamp=datetime.now().timestamp()))

@app.route('/_download_all')
def _download_all():
    def generate():
        temp_zip_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                temp_zip_path = temp_zip.name
                with zipfile.ZipFile(temp_zip, 'w') as zipf:
                    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, app.config['UPLOAD_FOLDER'])
                            zipf.write(file_path, arcname)
                            yield b''  # 生成空字节保持连接

                # 分块发送zip文件
                with open(temp_zip_path, 'rb') as f:
                    while True:
                        chunk = f.read(128*1024)  # 每次读取128KB
                        if not chunk:
                            break
                        yield chunk
        finally:
            if temp_zip_path and os.path.exists(temp_zip_path):
                try:
                    os.unlink(temp_zip_path)
                except Exception as e:
                    app.logger.error(f'临时文件删除失败: {str(e)}')

    response = Response(generate(), mimetype='application/zip')
    current_time = datetime.now()
    adjusted_time = adjust_time_for_timezone(current_time)  # 调整时区
    response.headers['Content-Disposition'] = f'attachment; filename=submissions_{adjusted_time.strftime("%Y%m%d_%H%M%S")}.zip'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
    response.headers['Connection'] = 'keep-alive'
    response.headers['X-Accel-Buffering'] = 'no'  # 禁用代理缓冲
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


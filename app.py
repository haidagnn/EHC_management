import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ehc_secret_key_123' # Trong thực tế phải giấu kỹ chuỗi này
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['CHALLENGE_FOLDER'] = 'static/challenges'

@app.route('/')
def index():
    return redirect(url_for('login'))

# Tạo thư mục nếu chưa có
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CHALLENGE_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- MODELS (Cấu trúc dữ liệu) ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False) # BÍ MẬT
    password_hash = db.Column(db.String(200), nullable=False)         # BÍ MẬT
    fullname = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='student') # 'teacher' hoặc 'student'

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    filename = db.Column(db.String(200))

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    filename = db.Column(db.String(200))
    submitted_at = db.Column(db.String(50)) # Lưu thời gian đơn giản

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hint = db.Column(db.String(200)) # Chỉ lưu gợi ý, KHÔNG LƯU ANSWER

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES CƠ BẢN (Đăng nhập/Đăng ký) ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        # Mã hóa mật khẩu trước khi lưu (Bảo mật cơ bản)
        hashed_pw = generate_password_hash(request.form['password'], method='scrypt')

        new_user = User(username=username, password_hash=hashed_pw,
                        fullname=request.form.get('fullname'), role='student')
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Sai thông tin đăng nhập!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- LOGIC BẢO MẬT HIỂN THỊ (ANTI-F12 / DATA LEAKAGE) ---

@app.route('/dashboard')
@login_required
def dashboard():
    # Lấy danh sách tất cả user từ Database
    all_users = User.query.all()

    # [QUAN TRỌNG]: Data Serialization
    # Chúng ta KHÔNG truyền biến 'all_users' trực tiếp sang HTML.
    # Vì User object chứa password_hash và username (nhạy cảm).
    # Ta phải tạo một list mới (safe_users) chỉ chứa info an toàn.

    safe_users = []
    for u in all_users:
        # Giả lập check trạng thái nộp bài (True/False)
        has_submitted = Submission.query.filter_by(user_id=u.id).first() is not None

        safe_info = {
            'id': u.id,
            'fullname': u.fullname,
            'email': u.email,
            'phone': u.phone,
            'role': u.role,
            'status': 'Đã nộp' if has_submitted else 'Chưa nộp'
        }
        safe_users.append(safe_info)

    # Chỉ gửi safe_users sang template
    return render_template('dashboard.html', users=safe_users)

# --- LOGIC PHÂN QUYỀN & IDOR ---

@app.route('/edit_user/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    # Check IDOR (Insecure Direct Object Reference)
    # Nếu là sinh viên, chỉ được sửa chính mình.
    if current_user.role == 'student' and current_user.id != user_id:
        return abort(403) # Chặn ngay lập tức

    user = User.query.get(user_id)
    if user:
        user.email = request.form['email']
        user.phone = request.form['phone']
        db.session.commit()
        flash('Cập nhật thành công!')
    return redirect(url_for('dashboard'))

# --- LOGIC CHALLENGE (FILE SYSTEM ANSWER) ---

@app.route('/challenge', methods=['GET', 'POST'])
@login_required
def challenge():
    if request.method == 'POST':
        # Logic dành cho Student: Giải đố
        user_input = request.form.get('answer', '')

        # [BẢO MẬT]: Input Sanitization
        # Chỉ cho phép a-z, 0-9. Loại bỏ dấu ., /, \ để chống Path Traversal
        # Nếu attacker nhập "../../etc/passwd", regex sẽ biến thành "etcpasswd" -> File không tồn tại -> An toàn.
        input_cleaned = re.sub(r'[^a-zA-Z0-9]', '', user_input)

        # Đường dẫn file cần tìm
        target_file = os.path.join(app.config['CHALLENGE_FOLDER'], f"{input_cleaned}.txt")

        # Kiểm tra sự tồn tại của file (Logic check đáp án)
        if os.path.exists(target_file):
            # Đọc nội dung file để hiển thị (Flag)
            with open(target_file, 'r', encoding='utf-8') as f:
                content = f.read()
            flash(f"CHÍNH XÁC! Nội dung bí mật là: {content}", "success")
        else:
            flash("SAI RỒI! Không tìm thấy file bí mật này.", "danger")

    # Lấy gợi ý để hiển thị
    chal = Challenge.query.first()
    hint = chal.hint if chal else "Chưa có gợi ý"
    return render_template('challenge.html', hint=hint)

@app.route('/upload_challenge', methods=['POST'])
@login_required
def upload_challenge():
    # Chỉ giáo viên được upload challenge
    if current_user.role != 'teacher':
        return abort(403)

    file = request.files['file']
    hint = request.form['hint']

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['CHALLENGE_FOLDER'], filename))

        # Lưu gợi ý vào DB, không lưu đáp án
        new_chal = Challenge(hint=hint)
        db.session.add(new_chal)
        db.session.commit()
        flash('Đã tạo thử thách!')

    return redirect(url_for('challenge'))

# Khởi chạy ứng dụng
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Tạo bảng Database nếu chưa có

        # Tạo sẵn 1 tài khoản Admin/Teacher để test
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password_hash=generate_password_hash('admin123'),
                         fullname='Thầy Giáo EHC', role='teacher', email='admin@ehc.vn')
            db.session.add(admin)
            db.session.commit()
            print("Đã tạo User mẫu: admin / admin123")

    app.run(debug=True)

@app.route('/view_submissions')
@login_required
def view_submissions():
    # Đây là trang hiển thị các bài nộp CTF mà bạn đang làm cho dự án EHC
    return render_template('view_submissions.html')
# EHC_management
Trải nghiệm thực tế (Live Demo)
Trang web đang hoạt động trực tiếp tại địa chỉ:

👉 hdagnnn.pythonanywhere.com/login

Tài khoản mẫu: admin / admin123

Tư duy tổ chức mã nguồn
Dự án được xây dựng với tiêu chí "Clean & Secure", giúp người mới bắt đầu dễ dàng tiếp cận cấu trúc một ứng dụng Flask thực tế:

app.py: File trung tâm chứa toàn bộ cấu hình, định nghĩa cơ sở dữ liệu và các luồng xử lý (Routes).

templates/: Chứa giao diện người dùng (HTML) được phân tách rõ ràng cho từng tính năng (Login, Register, Dashboard, Challenge).

static/: Quản lý các tệp tin tĩnh và hệ thống tệp tin phục vụ cho các bài tập thực hành bảo mật.

Phân tích tính năng Bảo mật (Security Audit)
Dự án này tập trung giải quyết các bài toán bảo mật web cơ bản nhưng cực kỳ quan trọng:

Chống IDOR (Insecure Direct Object Reference): Hệ thống kiểm tra quyền hạn (current_user.role) và mã định danh (current_user.id) để đảm bảo không ai có thể can thiệp vào dữ liệu của người khác.

Chống Path Traversal: Sử dụng Regex (re.sub) để làm sạch dữ liệu nhập vào từ người dùng, ngăn chặn việc truy cập trái phép vào các tệp tin hệ thống thông qua đường dẫn tương đối.

An toàn dữ liệu (Data Serialization): Thiết lập bộ lọc thông tin (safe_users) trước khi gửi dữ liệu sang phía người dùng, loại bỏ hoàn toàn nguy cơ rò rỉ các thông tin nhạy cảm như mã băm mật khẩu.

Bảo mật mật khẩu: Sử dụng phương pháp băm (hashing) mật khẩu trước khi lưu trữ, đảm bảo an toàn ngay cả khi cơ sở dữ liệu bị lộ.

Cách thiết lập môi trường Test (Local)
Khi bạn tải mã nguồn này về, hãy lưu ý các thư mục lưu trữ file:

Tạo các thư mục static/uploads và static/challenges nếu chúng chưa tồn tại.

Test Challenge: Hãy tạo một file .txt bất kỳ trong thư mục static/challenges (ví dụ: bi_mat.txt).

Nhập tên file (không kèm đuôi .txt) vào ô đáp án trên trang web để hệ thống kiểm tra và trả về kết quả.

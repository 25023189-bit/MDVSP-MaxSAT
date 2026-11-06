# =====================================================================
# KHỐI 1: THIẾT LẬP CƠ CHẾ NGẮT BỘ GIẢI THEO THỜI GIAN (TIMEOUT)
# =====================================================================

def interrupt_solver():
    # Hàm này dùng để ép bộ giải dừng quá trình tìm kiếm ngay lập tức.
    # Cần thiết vì bài toán SAT/Tối ưu có thể chạy vô tận nếu không có điểm dừng.
    print("Time out (3600s). Đang ngắt solver...")
    solver.interrupt()

time_limit = 3600.0  
# Chạy timer ở một luồng (thread) chạy ngầm độc lập. 
# Việc này giúp luồng chính vẫn có thể chạy lệnh solver.solve(), 
# và khi timer đếm ngược xong, nó sẽ tự động kích hoạt hàm interrupt_solver.
timer = threading.Timer(time_limit, interrupt_solver)

# =====================================================================
# KHỐI 2: THỰC THI BỘ GIẢI VÀ QUẢN LÝ THỜI GIAN
# =====================================================================

print("Bắt đầu giải...")
start_time = time.time() # Lưu thời điểm bắt đầu để đo lường tổng thời gian chạy.
timer.start() # Kích hoạt đồng hồ đếm ngược.

try:
    # Bắt đầu tìm nghiệm. Luồng chính sẽ bị block (chặn) tại đây cho đến khi:
    # 1. Tìm được nghiệm (hoặc chứng minh vô nghiệm).
    # 2. Bị ngắt bởi timer.
    solver.solve()
except Exception as e:
    # Bắt các lỗi ngoại lệ (ví dụ: solver bị crash) để chương trình không bị văng hoàn toàn.
    print(f"Lỗi thực thi: {e}")
finally:
    # Block finally luôn chạy dù try thành công hay thất bại.
    # Bắt buộc phải hủy timer nếu solver chạy xong trước 3600s để giải phóng luồng ngầm.
    timer.cancel()  
    end_time = time.time() # Chốt thời gian kết thúc.

# =====================================================================
# KHỐI 3: TRÍCH XUẤT VÀ ĐÁNH GIÁ KẾT QUẢ TỪ BỘ GIẢI
# =====================================================================

# Lấy kết quả nghiệm (nếu có) từ bộ nhớ của solver sau khi quá trình giải kết thúc/bị ngắt.
model = solver.get_model()

print(f"Thời gian chạy: {round(end_time - start_time, 2)}s")

if model:
    # Nếu model có giá trị -> Đã tìm được ít nhất 1 nghiệm thỏa mãn các ràng buộc cứng.
    print("Tìm thấy phương án.")
    print(f"Tổng chi phí: {solver.get_cost()}")
    
    print("Các biến được kích hoạt:")
    # Duyệt qua danh sách các biến (literals) trong nghiệm trả về.
    for lit in model:
        # lit > 0 mang ý nghĩa là biến Boolean đó có giá trị True (được chọn).
        # Những biến có giá trị âm (< 0) là False (không được chọn) nên ta bỏ qua.
        if lit > 0:
            # Dùng vpool.obj() để truy xuất lại tên hoặc đối tượng gốc từ mã ID của biến.
            print(vpool.obj(lit))
else:
    # Nếu model rỗng (None) -> Không có nghiệm nào được tìm thấy trong thời gian cho phép.
    print("Không tìm thấy phương án hợp lệ.")
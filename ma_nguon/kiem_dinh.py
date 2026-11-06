def kiem_dinh_nghiem(model, vpool):
    """
    Quy trình kiểm định nghiệm cho bài toán MDVSP theo CEGAR:
    - Giải mã nghiệm SAT thành các cung active (bật = 1).
    - Truy vết các đường đi P_k từ depot xuất phát đến depot kết thúc.
    - Phân loại: Nghiệm tối ưu nếu mọi d_start == d_end; ngược lại lưu danh sách phản ví dụ.
    """
    
    # =====================================================================
    # KHỐI 1: KHỞI TẠO CÁC BẢNG TRA CỨU NHANH (DICTIONARIES)
    # =====================================================================
    # Dùng dictionary giúp việc truy vết đường đi ở bước sau đạt độ phức tạp O(1)
    active_pout = {}   # Lưu mối quan hệ xuất bến: chuyến_đầu (j) -> bến_đầu (d_start)
    active_pin = {}    # Lưu mối quan hệ nhập bến: chuyến_cuối (i) -> bến_cuối (d_end)
    active_s = {}      # Lưu nối chuyến trung gian: chuyến_hiện_tại (i) -> chuyến_kế_tiếp (j)

    # =====================================================================
    # KHỐI 2: GIẢI MÃ MODEL (SAT MODEL DECODING)
    # =====================================================================
    for lit in model:
        # Trong SAT Solver, biến lit > 0 mang giá trị True (cung được kích hoạt chọn)
        if lit > 0:
            # Lấy tên biến tương ứng từ pool (Ví dụ: "Pout_d1_t2", "Pin_t5_d2", "s_t2_t3")
            var_name = vpool.obj(lit)
            
            # Bỏ qua các biến phụ (auxiliary variables) do solver tự sinh
            if var_name is None:
                continue
            
            parts = var_name.split("_")
            prefix = parts[0]

            if prefix == "Pout":
                d = f"{parts[1]}_{parts[2]}"
                j = f"{parts[3]}_{parts[4]}"
                active_pout[j] = d  
            elif prefix == "Pin":
                i = f"{parts[1]}_{parts[2]}"
                d = f"{parts[3]}_{parts[4]}"
                active_pin[i] = d   
            elif prefix == "s":
                i = f"{parts[1]}_{parts[2]}"
                j = f"{parts[3]}_{parts[4]}"
                active_s[i] = j

    # =====================================================================
    # KHỐI 3: TRUY VẾT DÒNG HÀNH TRÌNH XE (PATH TRACING)
    # =====================================================================
    danh_sach_duong_di = []
    phan_vi_du = []
    da_duyet = set()  # THÊM: Đánh dấu các chuyến đi đã được duyệt

    # Duyệt qua từng chuyến đi đầu tiên được kéo ra từ các bến xuất phát
    for j_start, d_start in active_pout.items():
        curr_trip = j_start
        chuoi_chuyen_di = [curr_trip]
        da_duyet.add(curr_trip)  # THÊM: Đánh dấu chuyến đầu tiên

        # Men theo các cung nối chuyến s_{i,j} để tìm chuỗi hành trình liên tục
        while curr_trip in active_s:
            curr_trip = active_s[curr_trip]  # Chuyển sang chuyến đi tiếp theo
            
            # THÊM: Tránh lặp vô tận nếu đồ thị bị xoắn vòng
            if curr_trip in da_duyet: 
                break
                
            chuoi_chuyen_di.append(curr_trip)
            da_duyet.add(curr_trip)  # THÊM: Đánh dấu chuyến tiếp theo

        # Lấy bến đích d_end tương ứng của chuyến cuối cùng trong chuỗi
        d_end = active_pin.get(curr_trip, None)

        # Đóng gói thông tin của hành trình P_k = (d_start -> i_1 -> ... -> i_l -> d_end)
        duong_di = {
            "loai": "tuyen_xe",  # THÊM: Đánh dấu đây là tuyến xe bình thường
            "d_start": d_start,
            "trips": chuoi_chuyen_di,
            "d_end": d_end
        }
        danh_sach_duong_di.append(duong_di)

        # =====================================================================
        # KHỐI 4: KIỂM TRA ĐIỀU KIỆN ĐÓNG BẾN (DEPOT CLOSURE CHECK)
        # =====================================================================
        # Nếu xe xuất phát ở bến d_start mà lại kết thúc ở bến d_end khác bến ban đầu,
        # đây chính là đường đi vi phạm và sẽ được trích xuất làm phản ví dụ cho CEGAR.
        if d_start != d_end:
            phan_vi_du.append(duong_di)

    # =====================================================================
    # KHỐI 4.5: QUÉT CHU TRÌNH CON LƠ LỬNG (SUBTOUR CATCHING)
    # =====================================================================
    # Quét lại các cung nối chuyến, nếu có chuyến chưa được duyệt từ bến thì đó là chu trình tàng hình
    for i, j in active_s.items():
        if i not in da_duyet:
            curr = i
            chu_trinh = []
            while curr not in da_duyet:
                chu_trinh.append(curr)
                da_duyet.add(curr)
                curr = active_s.get(curr)
                if curr is None: 
                    break
            
            if chu_trinh:
                phan_vi_du.append({
                    "loai": "chu_trinh_con", 
                    "trips": chu_trinh
                })

    # Nếu tập phản ví dụ rỗng -> Tất cả các xe đều về lại đúng bến ban đầu -> Tối ưu toàn cục
    toi_uu_toan_guc = (len(phan_vi_du) == 0)
    
    return toi_uu_toan_guc, danh_sach_duong_di, phan_vi_du
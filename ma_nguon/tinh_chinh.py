def tao_menh_de_tinh_chinh(phan_vi_du, reach_from, reach_to, vpool, D):
    """
    Tạo các mệnh đề tinh chỉnh (Refinement Clauses) từ danh sách phản ví dụ.
    Mục đích: Chặn các đường đi vi phạm tính đóng của bến xe trong lần giải SAT tiếp theo.
    """
    raw_clauses = []

    # Hàm hỗ trợ lấy ID biến từ vpool. Dấu âm (-) phía trước biểu thị phép phủ định (NOT) trong SAT.
    def var_S(i, j): return vpool.id(f"s_{i}_{j}")
    def var_Pout(d, j): return vpool.id(f"Pout_{d}_{j}")
    def var_Pin(i, d): return vpool.id(f"Pin_{i}_{d}")

    for item in phan_vi_du:
        loai = item.get("loai", "tuyen_xe")
        trips = item["trips"]  
        l = len(trips)

        # 1. XỬ LÝ CHU TRÌNH CON: Bắt buộc phải chặt đứt ít nhất 1 cung nối để phá vỡ vòng tròn
        if loai == "chu_trinh_con":
            clause = []
            for u in range(l):
                nxt = trips[(u + 1) % l]  # Lấy chuyến kế tiếp, chuyến cuối vòng lại chuyến đầu
                clause.append(-var_S(trips[u], nxt))
            raw_clauses.append(clause)
            continue  # Đã xử lý xong chu trình, bỏ qua phần dưới để sang phần tử tiếp theo
        
        # 2. XỬ LÝ TUYẾN XE BÌNH THƯỜNG (vi phạm điều kiện d_start != d_end)
        d_start = item["d_start"]
        d_end = item["d_end"]
        
        clause_da_tao = False

        # =================================================================
        # KHỐI 1: DEPOT-INDEPENDENT MUS
        # =================================================================
        # Tìm đoạn ngắn nhất i_a -> ... -> i_b mà không có depot nào vừa 
        # vươn tới được i_a lại vừa đón được i_b.
        for length in range(2, l + 1):
            for a in range(l - length + 1):
                b = a + length - 1
                i_a, i_b = trips[a], trips[b]

                # Kiểm tra xem có depot nào thỏa mãn cả 2 chiều hay không
                co_depot_chung = any(
                    (i_a in reach_from[d]) and (i_b in reach_to[d]) for d in D
                )

                if not co_depot_chung:
                    # Tạo mệnh đề bổ sung: Phủ định các cung nối chuyến bên trong đoạn này
                    clause = [-var_S(trips[u], trips[u + 1]) for u in range(a, b)]
                    raw_clauses.append(clause)
                    clause_da_tao = True
                    break
            if clause_da_tao:
                break
        
        if clause_da_tao: continue

        # =================================================================
        # KHỐI 2: PREFIX PRUNING (Cắt tỉa tiền tố)
        # =================================================================
        # Tìm vị trí r nhỏ nhất sao cho xe mất khả năng quay về bến gốc d_start.
        r_idx = l
        for idx in range(l):
            if trips[idx] not in reach_to[d_start]:
                r_idx = idx
                break

        if r_idx < l:
            # Tạo mệnh đề: Phủ định cung xuất bến d_start VÀ các cung nối chuyến tới r
            clause = [-var_Pout(d_start, trips[0])]
            if r_idx > 0:
                clause.extend([-var_S(trips[u], trips[u + 1]) for u in range(r_idx)])
            raw_clauses.append(clause)
            clause_da_tao = True

        if clause_da_tao: continue

        # =================================================================
        # KHỐI 3: SUFFIX PRUNING (Cắt tỉa hậu tố)
        # =================================================================
        # Tìm vị trí t lớn nhất sao cho bến đích d_end không thể vươn tới chuyến này.
        t_idx = -1
        for idx in range(l - 1, -1, -1):
            if trips[idx] not in reach_from[d_end]:
                t_idx = idx
                break

        if t_idx >= 0:
            # Tạo mệnh đề: Phủ định các cung nối chuyến từ t VÀ cung nhập bến d_end
            clause = []
            if t_idx < l - 1:
                clause.extend([-var_S(trips[u], trips[u + 1]) for u in range(t_idx, l - 1)])
            clause.append(-var_Pin(trips[-1], d_end))
            raw_clauses.append(clause)
            clause_da_tao = True

        if clause_da_tao: continue

        # =================================================================
        # KHỐI 4: FULL PATH EXCLUSION
        # =================================================================
        # Khi không thỏa mãn 3 điều kiện rút gọn trên, phủ định toàn bộ đường đi hiện tại.
        clause = [-var_Pout(d_start, trips[0])]
        clause.extend([-var_S(trips[u], trips[u + 1]) for u in range(l - 1)])
        clause.append(-var_Pin(trips[-1], d_end))
        raw_clauses.append(clause)

    # =================================================================
    # KHỐI 5: LỌC TRÙNG VÀ TRẢ VỀ
    # =================================================================
    # Chuyển các list thành tuple đã sắp xếp để dùng set lọc các mệnh đề trùng lặp
    unique_set = {tuple(sorted(c)) for c in raw_clauses}
    clauses_moi = [list(c) for c in unique_set]

    return clauses_moi
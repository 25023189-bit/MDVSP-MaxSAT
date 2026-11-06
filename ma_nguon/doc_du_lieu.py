import sys

def doc_du_lieu(file_path):
    # 1. KHỞI TẠO CÁC CẤU TRÚC DỮ LIỆU
    D = []
    T = []
    E_out = []
    E_in = []
    E_compat = []
    r = {}
    cost_out = {}
    cost_in = {}
    cost_compat = {}

    print(f"--> Đang mở file: {file_path}", flush=True)

    # 2. ĐỌC FILE VÀ CẮT DỮ LIỆU
    with open(file_path, "r") as f:
        raw_data = f.read().split()  # Cắt toàn bộ chữ và số thành danh sách

    num_depots = int(raw_data[0])
    num_trips = int(raw_data[1])
    print(f"--> Khởi tạo {num_depots} bến và {num_trips} chuyến đi...", flush=True)

    # Lấy danh sách Depot và số lượng xe (r)
    for d in range(num_depots):
        depot_name = f"depot_{d}"
        D.append(depot_name)
        r[depot_name] = int(raw_data[2 + d])

    # Lấy danh sách Chuyến đi (T)
    for i in range(num_trips):
        T.append(f"trip_{i}")

    # 3. QUÉT MA TRẬN CHI PHÍ
    total_nodes = num_depots + num_trips
    matrix_start_index = 2 + num_depots

    def get_node_name(index):
        if index < num_depots:
            return f"depot_{index}"
        return f"trip_{index - num_depots}"

    print("--> Đang quét ma trận chi phí (cập nhật tiến trình liên tục)...", flush=True)

    for i in range(total_nodes):
        # Đẩy tiến trình ra Terminal ngay lập tức mỗi 10 node
        if i % 10 == 0 or i == total_nodes - 1:
            phan_tram = int((i + 1) / total_nodes * 100)
            sys.stdout.write(f"\r    [Đọc file] Đang quét node {i+1}/{total_nodes} ({phan_tram}%) | Tìm thấy {len(E_compat)} cặp nối chuyến...")
            sys.stdout.flush()

        for j in range(total_nodes):
            idx = matrix_start_index + (i * total_nodes) + j

            if idx >= len(raw_data):
                break

            cost = int(raw_data[idx])

            if cost != -1:
                node_i = get_node_name(i)
                node_j = get_node_name(j)

                # Từ Bến -> Chuyến (Xuất bến)
                if i < num_depots and j >= num_depots:
                    E_out.append((node_i, node_j))
                    cost_out[(node_i, node_j)] = cost

                # Từ Chuyến -> Bến (Về bến)
                elif i >= num_depots and j < num_depots:
                    E_in.append((node_i, node_j))
                    cost_in[(node_i, node_j)] = cost

                # Từ Chuyến -> Chuyến (Nối chuyến)
                elif i >= num_depots and j >= num_depots:
                    E_compat.append((node_i, node_j))
                    cost_compat[(node_i, node_j)] = cost

    print(f"\n[HOÀN THÀNH] Đã đọc xong! Có {len(D)} bến, {len(T)} chuyến, và {len(E_compat)} cặp nối chuyến hợp lệ.", flush=True)

    # 4. TRẢ VỀ CÁC BIẾN DỮ LIỆU DẠNG TUPLE
    return D, T, E_out, E_in, E_compat, r, cost_out, cost_in, cost_compat
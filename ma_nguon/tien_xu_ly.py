import sys
from collections import defaultdict, deque

def tien_xu_li_do_thi(D, T, E_out, E_in, E_compat):
    """
    Tiền xử lý đồ thị: Loại bỏ các cung dư thừa và lập bảng tiếp cận.
    Thời gian thực thi đa thức tỷ lệ với kích thước đồ thị.
    """
    
    # =====================================================================
    # KHỐI 1: KHỞI TẠO DANH SÁCH KỀ (ADJACENCY LISTS)
    # =====================================================================
    # Chuyển đổi tập hợp các cung (Edges) thành dạng danh sách kề (Dict of Lists) 
    # Việc này nhằm giảm độ phức tạp khi cần duyệt lặp lại các cung liền kề ở Bước 2 & 3.
    next_trips = defaultdict(list)
    prev_trips = defaultdict(list)
    trips_from_depot = defaultdict(list)
    trips_to_depot = defaultdict(list)

    for u, v in E_compat:
        next_trips[u].append(v)
        prev_trips[v].append(u)
        
    for d, j in E_out:
        trips_from_depot[d].append(j)
        
    for i, d in E_in:
        trips_to_depot[d].append(i)

    # =====================================================================
    # KHỐI 2: XÂY DỰNG BẢNG REACHFROM (DUYỆT BFS CHIỀU TIẾN)
    # =====================================================================
    # Nhiệm vụ: Tìm tất cả các chuyến đi mà depot 'd' có thể vươn tới.
    reach_from = {}
    for d in D:
        reach_from[d] = set()
        queue = deque()
        
        # Bước 2a: Nạp các chuyến đi trực tiếp từ bến d vào hàng đợi
        for trip in trips_from_depot[d]:
            reach_from[d].add(trip)
            queue.append(trip)
            
        # Bước 2b: Dùng thuật toán BFS để lan truyền qua các cung E_compat
        while queue:
            u = queue.popleft()  
            for v in next_trips[u]:
                if v not in reach_from[d]:
                    reach_from[d].add(v) 
                    queue.append(v)  

    # =====================================================================
    # KHỐI 3: XÂY DỰNG BẢNG REACHTO (DUYỆT BFS CHIỀU LÙI)
    # =====================================================================
    # Nhiệm vụ: Tìm tất cả các chuyến đi mà từ đó tồn tại đường đi quay về depot 'd'.
    reach_to = {}
    for d in D:
        reach_to[d] = set()
        queue = deque()
        
        # Bước 3a: Nạp các chuyến đi cắm trực tiếp vào bến d
        for trip in trips_to_depot[d]:
            reach_to[d].add(trip)
            queue.append(trip)
            
        # Bước 3b: Lan truyền ngược lên phía trước qua các cung E_compat
        while queue:
            v = queue.popleft()
            for u in prev_trips[v]:
                if u not in reach_to[d]:
                    reach_to[d].add(u)
                    queue.append(u)

    # =====================================================================
    # KHỐI 4: LỌC TĨNH CUNG BẤT KHẢ THI (STATIC FILTERING)
    # =====================================================================
    # Một cung chỉ được giữ lại nếu nó có khả năng nằm trong một hành trình khép kín, 
    # tức là có bến để xuất phát và quay về.
    E_out_loc = []
    E_in_loc = []
    E_compat_loc = []

    # 1. Lọc cung xuất bến: Bỏ (d, j) nếu chuyến j không thể tìm đường quay lại bến d
    for d, j in E_out:
        if j in reach_to[d]:
            E_out_loc.append((d, j))
            
    # 2. Lọc cung nhập bến: Bỏ (i, d) nếu bến d không thể vươn tới chuyến i từ trước
    for i, d in E_in:
        if i in reach_from[d]:
            E_in_loc.append((i, d))
            
    # 3. Lọc cung tương thích: Bỏ (i, j) nếu không có bất kỳ depot 'd' nào thỏa mãn
    # việc vừa vươn tới được i, lại vừa đón được j quay về.
    for i, j in E_compat:
        chung_ben = False
        for d in D:
            if (i in reach_from[d]) and (j in reach_to[d]):
                chung_ben = True
                break  
                
        if chung_ben:
            E_compat_loc.append((i, j))
            
    # Trả về đồ thị đã thu gọn và 2 bảng Reachability để phục vụ kiểm định CEGAR sau này
    return E_out_loc, E_in_loc, E_compat_loc, reach_from, reach_to
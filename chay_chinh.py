import sys
import os
import time

# Thiết lập đường dẫn tương đối để import module nội bộ
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "ma_nguon"))

from doc_du_lieu import doc_du_lieu
from tien_xu_ly import tien_xu_li_do_thi
from xay_dung_mo_hinh import tao_mo_hinh_maxsat
from kiem_dinh import kiem_dinh_nghiem
from tinh_chinh import tao_menh_de_tinh_chinh

def giai_va_kiem_dinh(solver, vpool, D, reach_from, reach_to, max_iterations=100, time_limit=3600):
    """
    Thực thi vòng lặp CEGAR: Giải mô hình trừu tượng -> Kiểm định nghiệm -> Tinh chỉnh.
    Kết thúc khi tìm được nghiệm tối ưu toàn cục hoặc hết thời gian.
    """
    start_time = time.time()
    vong_lap = 1
    best_solution = None

    print(f"Bắt đầu vòng lặp CEGAR (Tối đa {max_iterations} vòng, giới hạn {time_limit}s)...")

    while vong_lap <= max_iterations:
        elapsed_time = time.time() - start_time

        # =================================================================
        # KHỐI 1: KIỂM SOÁT THỜI GIAN (TIMEOUT)
        # =================================================================
        if elapsed_time > time_limit:
            print(f"\nTimeout: Đã chạy {elapsed_time:.2f}s (giới hạn {time_limit}s).")
            break

        print(f"\n--- VÒNG {vong_lap} ({elapsed_time:.2f}s) ---")

        # =================================================================
        # KHỐI 2: GIẢI MÔ HÌNH BẰNG MAXSAT SOLVER
        # =================================================================
        # Yêu cầu bộ giải tìm nghiệm thỏa mãn cho Bài toán trừu tượng hiện tại
        t_solve = time.time()
        is_sat = solver.solve()
        
        if not is_sat:
            print("Trạng thái: UNSAT (Không tìm thấy phương án thỏa mãn).")
            break

        model = solver.get_model()
        if not model:
            print("Lỗi: Bộ giải trả về SAT nhưng không trích xuất được model.")
            break

        current_cost = solver.get_cost()
        print(f"Thời gian giải SAT: {time.time() - t_solve:.2f}s. Chi phí hiện tại: {current_cost}")

        # =================================================================
        # KHỐI 3: KIỂM ĐỊNH NGHIỆM
        # =================================================================
        # Phân rã đồ thị kết quả thành các chuỗi đường đi không giao nhau
        toi_uu, danh_sach_duong_di, phan_vi_du = kiem_dinh_nghiem(model, vpool)
        best_solution = danh_sach_duong_di

        so_tuyen_dung = len(danh_sach_duong_di) - len(phan_vi_du)
        print(f"Kiểm định: {so_tuyen_dung} tuyến hợp lệ, {len(phan_vi_du)} tuyến vi phạm bến (d_start != d_end).")

        # =================================================================
        # KHỐI 4: PHÂN NHÁNH KẾT QUẢ (TỐI ƯU TOÀN CỤC HOẶC TINH CHỈNH)
        # =================================================================
        if toi_uu:
            # Nếu tất cả các đường đi đều có d_start == d_end -> Kết thúc CEGAR
            print(f"\n[THÀNH CÔNG] TÌM THẤY NGHIỆM TỐI ƯU TOÀN CỤC SAU {vong_lap} VÒNG LẶP.")
            print(f"Tổng chi phí: {current_cost}")
            print("Danh sách tuyến xe:")
            for idx, path in enumerate(danh_sach_duong_di, 1):
                print(f"  Tuyến {idx}: Bến {path['d_start']} -> Chuyến {path['trips']} -> Bến {path['d_end']}")
            return danh_sach_duong_di
        else:
            # Nếu tồn tại đường đi vi phạm -> Chuyển sang bước tinh chỉnh
            t_refine = time.time()
            clauses_moi = tao_menh_de_tinh_chinh(phan_vi_du, reach_from, reach_to, vpool, D)
            
            # Đưa các mệnh đề cắt tỉa bổ sung ngược lại vào solver để thu hẹp không gian tìm kiếm
            for clause in clauses_moi:
                solver.add_clause(clause)
                
            print(f"Tinh chỉnh: Đã thêm {len(clauses_moi)} mệnh đề vào solver ({time.time() - t_refine:.2f}s).")

        vong_lap += 1

    # Nếu vòng lặp bị ngắt (do timeout), trả về kết quả khả thi nhất tạm thời
    if best_solution:
        print("\n[KẾT QUẢ TẠM THỜI] Các tuyến xe từ vòng lặp cuối:")
        for idx, path in enumerate(best_solution, 1):
            hop_le = "Hợp lệ" if path['d_start'] == path['d_end'] else "Vi phạm"
            print(f"  [{hop_le}] Tuyến {idx}: Bến {path['d_start']} -> Chuyến {path['trips']} -> Bến {path['d_end']}")
        return best_solution

    return None

def main():
    print("BẮT ĐẦU QUÁ TRÌNH GIẢI BÀI TOÁN MDVSP BẰNG CEGAR\n")
    t0 = time.time()

    # Bước 1: Đọc dữ liệu
    file_path = os.path.join(current_dir, "du_lieu", "du_lieu_mau.inp")
    try:
        D, T, E_out, E_in, E_compat, r, cost_out, cost_in, cost_compat = doc_du_lieu(file_path)
        print("1. Đọc dữ liệu hoàn tất.")
    except Exception as e:
        print(f"Lỗi đọc dữ liệu: {e}")
        return

    # Bước 2: Tiền xử lý đồ thị
    try:
        E_out_loc, E_in_loc, E_compat_loc, reach_from, reach_to = tien_xu_li_do_thi(D, T, E_out, E_in, E_compat)
        print("2. Tiền xử lý đồ thị hoàn tất.")
    except Exception as e:
        print(f"Lỗi tiền xử lý: {e}")
        return

    # Bước 3: Xây dựng mô hình
    try:
        solver, vpool = tao_mo_hinh_maxsat(D, T, E_out_loc, E_in_loc, E_compat_loc, r, cost_out, cost_in, cost_compat)
        print("3. Xây dựng mô hình MaxSAT hoàn tất.\n")
    except Exception as e:
        print(f"Lỗi xây dựng mô hình: {e}")
        return

    # Bước 4: Chạy CEGAR
    giai_va_kiem_dinh(solver, vpool, D, reach_from, reach_to, max_iterations=100, time_limit=3600)

    print(f"\nTỔNG THỜI GIAN CHẠY: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    main()
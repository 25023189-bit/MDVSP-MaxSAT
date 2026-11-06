import sys
from collections import defaultdict
from hermax.incremental import EvalMaxSAT
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType

def tao_mo_hinh_maxsat(D, T, E_out, E_in, E_compat, r, cost_out, cost_in, cost_compat):
    """
    Xây dựng Mô hình trừu tượng cơ sở (MaxSAT):
    - Soft clauses: Tối thiểu hóa tổng chi phí hành trình.
    - Hard clauses: Bảo toàn luồng và giới hạn số lượng xe tại depot.
    """
    solver = EvalMaxSAT()
    vpool = IDPool()
    print (f"E={len(E_out + E_compat + E_in)}")

    # Hàm hỗ trợ tạo ID số nguyên cho các biến quyết định Boolean (0, 1)
    def var_S(i, j): return vpool.id(f"s_{i}_{j}")
    def var_Pout(d, j): return vpool.id(f"Pout_{d}_{j}")
    def var_Pin(i, d): return vpool.id(f"Pin_{i}_{d}")

    # =====================================================================
    # KHỐI 1: HÀM MỤC TIÊU (SOFT CLAUSES)
    # =====================================================================
    # MaxSAT mặc định tối đa hóa tổng trọng số các mệnh đề đúng. 
    # Để "tối thiểu hóa" hàm mục tiêu chi phí, ta đưa vào phủ định của biến (-var).
    # Nếu bộ giải kích hoạt biến này (nghĩa là chọn cung đó), mệnh đề phủ định sẽ False,
    # khiến bộ giải bị "phạt" một lượng điểm đúng bằng chi phí của cung đó.
    c = 0
    for d, j in E_out:
        weight = int(round(cost_out[(d, j)]))
        if weight > 0:
            solver.set_soft(-var_Pout(d, j), weight=weight)
            c+=1
    for i, d in E_in:
        weight = int(round(cost_in[(i, d)]))
        if weight > 0:
            solver.add_clause([-var_Pin(i, d)], weight=weight)
            c+= 1
    for i, j in E_compat:
        weight = int(round(cost_compat[(i, j)]))
        if weight > 0:
            solver.add_clause([-var_S(i, j)], weight=weight)
            c+=1

    print(f"c={c}")
    # =====================================================================
    # KHỐI 2: GOM NHÓM BIẾN VÀO BẢNG TRA CỨU (Tối ưu độ phức tạp)
    # =====================================================================
    # Nhóm sẵn các biến tập trung theo từng chuyến đi (T) và bến xe (D).
    # Kỹ thuật này giúp vòng lặp tạo Hard Clause ở Khối 3 và 4 chạy trong O(E) thay vì O(N^2).
    lits_in_map = defaultdict(list)
    lits_out_map = defaultdict(list)
    depot_pout_map = defaultdict(list)
    depot_pin_map = defaultdict(list)

    for i, j in E_compat:
        lit = var_S(i, j)
        lits_in_map[j].append(lit)
        lits_out_map[i].append(lit)

    for d, j in E_out:
        lit = var_Pout(d, j)
        lits_in_map[j].append(lit)
        depot_pout_map[d].append(lit)

    for i, d in E_in:
        lit = var_Pin(i, d)
        lits_out_map[i].append(lit)
        depot_pin_map[d].append(lit)

    # =====================================================================
    # KHỐI 3: RÀNG BUỘC CƠ SỞ - BẢO TOÀN LUỒNG (HARD CLAUSES)
    # =====================================================================
    # Đảm bảo bảo toàn luồng vào (In-flow): Bằng đúng 1 cho mỗi chuyến đi j.
    for j in T:
        lits_in = lits_in_map[j]
        if lits_in:
            # CardEnc.equals với bound=1 mã hóa điều kiện "Tổng các biến = 1"
            cnf = CardEnc.equals(lits=lits_in, bound=1, vpool=vpool, encoding=EncType.seqcounter)
            for clause in cnf.clauses:
                solver.add_clause(clause)

    # Đảm bảo bảo toàn luồng ra (Out-flow): Bằng đúng 1 cho mỗi chuyến đi i.
    for i in T:
        lits_out = lits_out_map[i]
        if lits_out:
            cnf = CardEnc.equals(lits=lits_out, bound=1, vpool=vpool, encoding=EncType.seqcounter)
            for clause in cnf.clauses:
                solver.add_clause(clause)

    # =====================================================================
    # KHỐI 4: RÀNG BUỘC CƠ SỞ - GIỚI HẠN SỐ XE TẠI DEPOT (HARD CLAUSES)
    # =====================================================================
    # Đảm bảo số lượng xe xuất bến và nhập bến tại depot d không vượt quá r[d]
    for d in D:
        # Giới hạn số xe xuất bến (Pout <= r_d)
        lits_pullout = depot_pout_map[d]
        if lits_pullout:
            # CardEnc.atmost với bound=r[d] mã hóa điều kiện "Tổng các biến <= r[d]"
            cnf = CardEnc.atmost(lits=lits_pullout, bound=r[d], vpool=vpool, encoding=EncType.seqcounter)
            for clause in cnf.clauses:
                solver.add_clause(clause)

        # Giới hạn số xe nhập bến (Pin <= r_d)
        lits_pullin = depot_pin_map[d]
        if lits_pullin:
            cnf = CardEnc.atmost(lits=lits_pullin, bound=r[d], vpool=vpool, encoding=EncType.seqcounter)
            for clause in cnf.clauses:
                solver.add_clause(clause)

    return solver, vpool
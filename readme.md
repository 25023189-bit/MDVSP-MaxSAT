\# Mã hóa SAT/MaxSAT cho bài toán Lập lịch xe nhiều bến (MDVSP)



> \*\*Trạng thái: kết quả âm tính (negative result).\*\*

> Phương pháp đúng về mặt lý thuyết nhưng \*\*không mở rộng được\*\* với bài toán kích thước lớn do số biến và số mệnh đề tăng quá nhanh. Repo được công khai để người khác tham khảo, tránh lặp lại hướng đi này và có thể phát triển tiếp.



\## 1. Bài toán



\*\*Multiple Depot Vehicle Scheduling Problem (MDVSP)\*\* với một loại xe đồng nhất: gán các chuyến đi (trips) đã có lịch cố định cho các xe đặt tại nhiều bến (depots) sao cho:



\- Mỗi chuyến đi được phục vụ đúng một lần (bao phủ).

\- Mỗi xe xuất phát từ một bến và \*\*phải quay về đúng bến đó\*\*.

\- Số xe xuất phát từ bến `d` không vượt quá `r\_d`.

\- Hai chuyến liên tiếp trên cùng một xe phải tương thích về thời gian và di chuyển.

\- \*\*Tối thiểu hóa\*\* tổng chi phí chờ và chạy rỗng (gồm chi phí rời bến, về bến và nối chuyến).



Tài liệu tham khảo chính:



\- Kulkarni, Krishnamoorthy, Ranade, Ernst, Patil (2018). \*A new formulation and a column generation-based heuristic for the multiple depot vehicle scheduling problem.\* Transportation Research Part B, 118, 457–487.

\- Laurent, B. \& Hao, J.-K. (2009). \*Iterated local search for the multiple depot vehicle scheduling problem.\* Computers \& Industrial Engineering, 57, 277–286.



\## 2. Hướng tiếp cận



Thay vì dùng LP/MIP hay sinh cột như các bài báo trên, dự án thử \*\*mã hóa bài toán thành MaxSAT\*\* và giải bằng vòng lặp \*\*CEGAR\*\* (Counter-Example Guided Abstraction Refinement).



\### Mô hình SAT



Biến Boolean (trên đồ thị gồm các cung hợp lệ):



| Biến | Ý nghĩa |

|---|---|

| `s\_{i,j}` | Chuyến `j` được chạy ngay sau chuyến `i` trên cùng một xe |

| `Pout\_{d,j}` | Xe xuất bến `d` để chạy chuyến đầu tiên là `j` |

| `Pin\_{i,d}` | Xe kết thúc ở chuyến `i` rồi về bến `d` |



Ràng buộc cứng (hard clauses):



\- \*\*Bảo toàn luồng vào:\*\* mỗi chuyến `j` có đúng một cung đi vào (từ chuyến khác hoặc từ bến).

\- \*\*Bảo toàn luồng ra:\*\* mỗi chuyến `i` có đúng một cung đi ra (sang chuyến khác hoặc về bến).

\- \*\*Sức chứa bến:\*\* số cung `Pout` (và `Pin`) của mỗi bến không vượt quá `r\_d`.



Ràng buộc mềm (soft clauses): mỗi cung được chọn bị phạt bằng đúng chi phí của nó, nên MaxSAT tối thiểu hóa tổng chi phí.



\### Vòng lặp CEGAR



Mô hình cơ sở \*\*chưa\*\* ép điều kiện "xe về đúng bến xuất phát". Điều kiện này được bổ sung dần:



1\. Giải mô hình MaxSAT hiện tại.

2\. \*\*Kiểm định nghiệm\*\* (`kiem\_dinh.py`): truy vết từng tuyến xe, tìm các tuyến có `d\_start != d\_end` và các chu trình con.

3\. Nếu không có vi phạm: đây là nghiệm tối ưu toàn cục, dừng.

4\. Nếu có: sinh \*\*mệnh đề tinh chỉnh\*\* (`tinh\_chinh.py`) để loại các đường đi vi phạm (cắt tỉa tiền tố/hậu tố, loại cả đường đi, phá chu trình con), thêm vào solver và quay lại bước 1.



\*\*Tiền xử lý\*\* (`tien\_xu\_ly.py`): dùng BFS tính hai bảng `reach\_from\[d]` và `reach\_to\[d]` để loại sớm các cung không thể nằm trong hành trình khép kín qua một bến nào đó.



\## 3. Cấu trúc thư mục



```

.

├── chay\_chinh.py          # Điểm vào: đọc dữ liệu -> tiền xử lý -> dựng mô hình -> CEGAR

├── ma\_nguon/

│   ├── \_\_init\_\_.py

│   ├── doc\_du\_lieu.py       # Đọc file instance (.inp)

│   ├── tien\_xu\_ly.py        # Tiền xử lý đồ thị, bảng reach\_from / reach\_to

│   ├── xay\_dung\_mo\_hinh.py  # Dựng mô hình MaxSAT cơ sở

│   ├── kiem\_dinh.py         # Giải mã nghiệm, truy vết tuyến, tìm phản ví dụ

│   ├── tinh\_chinh.py        # Sinh mệnh đề tinh chỉnh

│   └── giai\_mo\_hinh.py      # Đoạn mã giải có timeout dùng thử riêng (không dùng trong chay\_chinh.py)

├── du\_lieu/

│   └── du\_lieu\_mau.inp      # File instance đầu vào

└── tai\_lieu/                # Báo cáo phân tích bài toán và mô hình SAT (PDF/DOCX)

```



> `chay\_chinh.py` thêm thư mục `ma\_nguon/` vào `sys.path` và đọc dữ liệu từ `du\_lieu/du\_lieu\_mau.inp`. Hãy giữ đúng cấu trúc trên hoặc chỉnh lại đường dẫn trong `main()`.



\## 4. Cài đặt và chạy



Yêu cầu: Python 3.9+.



Thư viện sử dụng:



\- \[\*\*Hermax\*\*](https://hermax.readthedocs.io): thư viện Python cho MaxSAT, dùng solver `EvalMaxSAT` qua `hermax.incremental` (hỗ trợ thêm mệnh đề dần trong vòng lặp CEGAR).

\- \[\*\*PySAT\*\*](https://pysathq.github.io): dùng `IDPool` để quản lý biến và `CardEnc` để mã hóa ràng buộc đếm.



```bash

pip install hermax python-sat

```



Chạy:



```bash

python chay\_chinh.py

```



Tham số mặc định trong `chay\_chinh.py`: tối đa \*\*100 vòng lặp CEGAR\*\* và giới hạn \*\*3600 giây\*\*.



\### Định dạng file đầu vào (`.inp`)



File gồm các số cách nhau bởi khoảng trắng:



1\. `m` (số bến), `n` (số chuyến).

2\. `m` số: số xe `r\_d` của từng bến.

3\. Ma trận chi phí kích thước `(m + n) x (m + n)`, đọc theo từng hàng. Các chỉ số `0..m-1` là bến, `m..m+n-1` là chuyến. Giá trị `-1` nghĩa là không có cung.



Bộ dữ liệu chuẩn tham khảo: các instance MDVSP được dùng trong Pepin et al. (2008) và Laurent \& Hao (2009), tải tại http://people.few.eur.nl/huisman/instances.htm.



\## 5. Kết quả và vì sao không mở rộng được



\- \*\*Đồ thị nhỏ:\*\* với các instance có ít bến và ít chuyến, số cung, số biến và số mệnh đề còn ít nên MaxSAT solver giải được, vòng lặp CEGAR hội tụ và cho nghiệm tối ưu.

\- \*\*Đồ thị lớn hơn:\*\* số biến và số mệnh đề \*\*bùng nổ\*\*, solver không tìm được nghiệm trong thời gian cho phép (hoặc mô hình quá lớn để dựng/giải). Phương pháp không cho ra kết quả với các instance cỡ lớn.



Nguyên nhân chính:



\- Số cung nối chuyến `E\_compat` tăng gần bậc hai theo số chuyến `n`, kéo theo số biến `s\_{i,j}` và số mệnh đề mã hóa ràng buộc đếm (sequential counter) tăng rất nhanh.

\- Vòng lặp CEGAR cần nhiều vòng tinh chỉnh vì ràng buộc "về đúng bến" không có trong mô hình cơ sở; mỗi vòng lại gọi MaxSAT solver trên một mô hình đã rất lớn.

\- Bài toán có cấu trúc luồng mạng với mục tiêu số học, nên LP/MIP kết hợp sinh cột (Kulkarni et al., 2018) thường hiệu quả hơn SAT thuần ở quy mô lớn.



\## 6. Hướng phát triển có thể thử



\- Giảm số biến: lọc cung mạnh hơn, phá đối xứng, mô hình thời gian-không gian gọn hơn (xem inventory formulation của Kulkarni et al.).

\- Mã hóa gọn hơn cho ràng buộc đếm.

\- Kết hợp SAT với LP: dùng SAT khởi tạo cột cho sinh cột, hoặc Logic-based Benders Decomposition.

\- Dùng nghiệm heuristic (ví dụ ILS) làm cận trên ban đầu cho MaxSAT.



\## 7. Đóng góp



\- \*\*Mô hình SAT và ý tưởng phương pháp:\*\* Nguyễn Kim Trung Đức.

\- \*\*Cài đặt code và chạy thực nghiệm:\*\* Bùi Thế Dũng.



\## 8. Trích dẫn



Nếu sử dụng lại, vui lòng trích dẫn Hermax:



```bibtex

@InProceedings{salviahornos\_et\_al:LIPIcs.SAT.2026.41,

&#x20; author = {Salvia Hornos, Josep Maria and Fern\\'{a}ndez Cam\\'{o}n, C\\`{e}sar and Mateu Pi\\\~{n}ol, Carles},

&#x20; title = {{Hermax: A Unified MaxSAT Library}},

&#x20; booktitle = {29th International Conference on Theory and Applications of Satisfiability Testing (SAT 2026)},

&#x20; year = {2026},

&#x20; doi = {10.4230/LIPIcs.SAT.2026.41}

}

```



Hãy trích dẫn thêm bài báo của solver backend mà bạn dùng (xem tài liệu Hermax).



\## 9. Giấy phép



Dự án được phát hành theo giấy phép \[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).


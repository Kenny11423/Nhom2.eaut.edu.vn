# KẾ HOẠCH CHI TIẾT DỰ ÁN: PHẦN MỀM QUẢN LÝ BÁN VÉ TÀU HỎA

**Nhóm thực hiện:**
1. **Trần Long Vũ** (Nhóm trưởng)
2. **Phạm Quang Huy**
3. **Phạm Đức Huy**

---

## TUẦN 1: PHÂN TÍCH NGHIỆP VỤ & THIẾT KẾ CƠ SỞ DỮ LIỆU (DATABASE)
*Mục tiêu: Xây dựng nền móng dữ liệu vững chắc và cấu trúc Class.*

| Thành viên | Nhiệm vụ cụ thể | Sản phẩm bàn giao |
| :--- | :--- | :--- |
| **Trần Long Vũ** | - Phân tích chi tiết chức năng.<br>- Thiết kế cấu trúc các Lớp (Class Diagram) trong code. | Bản mô tả chức năng & Sơ đồ Class. |
| **Phạm Quang Huy** | - Khảo sát và liệt kê các trường dữ liệu cần thiết.<br>- Phác thảo luồng đi của dữ liệu từ UI vào DB. | Danh mục dữ liệu & Luồng nghiệp vụ. |
| **Phạm Đức Huy** | - **Trọng tâm:** Thiết kế sơ đồ thực thể ERD.<br>- Cài đặt Database và viết Script tạo bảng (SQL/File). | **Sơ đồ ERD & File Database.** |

---

## TUẦN 2: LẬP TRÌNH LOGIC (BACKEND) & THIẾT KẾ UI
*Mục tiêu: Cả 3 cùng bắt đầu code các thành phần nền tảng.*

| Thành viên | Nhiệm vụ cụ thể | Sản phẩm bàn giao |
| :--- | :--- | :--- |
| **Trần Long Vũ** | - **Coding:** Lập trình Logic nghiệp vụ lõi (Tính toán giá vé, Kiểm tra chỗ trống, Xử lý đặt vé). | Mã nguồn Core Logic. |
| **Phạm Quang Huy** | - Vẽ Mockup UI hoàn chỉnh.<br>- **Coding:** Lập trình khung giao diện cơ bản (Base Windows, Frames) bằng Tkinter/Qt. | Mockup UI & Mã nguồn khung giao diện. |
| **Phạm Đức Huy** | - **Coding:** Lập trình tầng truy xuất dữ liệu (DAO/Repository) để đọc/ghi dữ liệu từ DB đã tạo ở Tuần 1. | Mã nguồn Database Access. |

---

## TUẦN 3: LẬP TRÌNH FRONTEND (GIAO DIỆN) & TÍCH HỢP HỆ THỐNG
*Mục tiêu: Hoàn thiện code giao diện và kết nối toàn bộ hệ thống.*

| Thành viên | Nhiệm vụ cụ thể | Sản phẩm bàn giao |
| :--- | :--- | :--- |
| **Trần Long Vũ** | - **Coding:** Tích hợp Logic vào Giao diện.<br>- Kiểm thử (Testing) & Sửa lỗi hệ thống. | Bản Demo hoàn chỉnh & Báo cáo test. |
| **Phạm Quang Huy** | - **Coding:** Lập trình chi tiết các màn hình cho Người dùng (Tìm kiếm, Đặt vé, Xem lịch trình). | Mã nguồn Frontend (User). |
| **Phạm Đức Huy** | - **Coding:** Lập trình chi tiết các màn hình cho Admin (Quản lý tàu, Quản lý doanh thu, Thống kê). | Mã nguồn Frontend (Admin). |


---

## TIÊU CHÍ ĐÁNH GIÁ (Bám sát product.md)
*   **Chức năng & Giao diện (1.0đ):** Quang Huy chủ trì giao diện, Vũ đảm bảo đủ chức năng.
*   **Thiết kế hệ thống (1.0đ):** Đức Huy (DB) & Vũ (Class) phối hợp.
*   **Cấu trúc mã nguồn (1.0đ):** Cả 3 thành viên đều có đóng góp code rõ ràng, tổ chức theo Module.
*   **Kiểm thử & Demo (1.0đ):** Long Vũ thực hiện với dữ liệu thật từ DB của Đức Huy.

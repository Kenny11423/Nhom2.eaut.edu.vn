# Phân chia công việc tuần 3 cho 3 người

Mục tiêu: hoàn thiện backend nghiệp vụ, phần quản lý dữ liệu và luồng tạo hành trình để có thể demo đầy đủ ứng dụng tuần 3.

Nguyên tắc chia việc:

- Mỗi người phụ trách một nhóm chức năng rõ ràng để dễ commit và nghiệm thu
- Hạn chế sửa chồng chéo cùng một phần trong cùng thời điểm
- Mỗi phần việc đều gắn với một luồng nghiệp vụ có thể demo trực tiếp

## Phạm Đức Huy - Quản lý các đối tượng

**Phạm vi chịu trách nhiệm**

- Quản lý các đối tượng `Trains`, `Carriages`, `Stations`
- Hoàn thiện các chức năng thêm, hiển thị, xóa dữ liệu trong tab danh mục
- Đồng bộ danh sách tàu, toa, ga với dữ liệu thực tế trong database
- Kiểm tra ràng buộc khi xóa dữ liệu đang được dùng trong hành trình hoặc chuyến tàu

**File phụ trách**

- `src/train_ticket_app/main_window.py`
- `src/train_ticket_app/backend/service.py`

**Commit gợi ý**

- `feat(catalog): quan ly trains carriages stations`

## Phạm Quang Huy - Lập hành trình

**Phạm vi chịu trách nhiệm**

- Xây dựng chức năng lập hành trình mới cho chuyến tàu
- Thiết kế luồng chọn tàu, chọn ga dừng, chọn toa từ danh sách có sẵn
- Gắn danh sách ga theo thứ tự dừng và danh sách toa cho từng chuyến
- Đảm bảo tạo được chuyến mới và sinh đủ dữ liệu ghế theo toa của chuyến

**File phụ trách**

- `src/train_ticket_app/main_window.py`
- `src/train_ticket_app/backend/service.py`
- `src/train_ticket_app/backend/database.py`

**Commit gợi ý**

- `feat(trip): lap hanh trinh moi va gan toa cho chuyen`

## Trần Long Vũ - Đặt vé và nghiệp vụ bán vé

**Phạm vi chịu trách nhiệm**

- Hoàn thiện nghiệp vụ tra cứu chuyến tàu
- Hoàn thiện luồng đặt vé `chọn toa -> chọn ghế`
- Xử lý hủy vé, cập nhật trạng thái ghế và danh sách vé
- Kiểm tra tính đúng đắn của dữ liệu vé theo từng chặng trong hành trình

**File phụ trách**

- `src/train_ticket_app/main_window.py`
- `src/train_ticket_app/backend/service.py`
- `src/train_ticket_app/backend/bridge.py`

**Commit gợi ý**

- `feat(booking): dat ve theo luong chon toa chon ghe`

## Kết quả mong muốn sau tuần 3

- Quản lý được danh mục ga, tàu, toa
- Lập được hành trình mới bằng cách chọn từ danh sách có sẵn
- Gán được nhiều toa cho từng chuyến
- Tra cứu được chuyến tàu theo ga đi, ga đến và ngày đi
- Đặt vé theo luồng chọn toa rồi chọn ghế
- Hủy vé được và cập nhật lại dữ liệu liên quan

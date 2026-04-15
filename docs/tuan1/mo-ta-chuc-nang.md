# Tuần 1 - Mô tả chức năng

## 1. Tổng quan đề tài

**Tên đề tài:** Phần mềm quản lý bán vé tàu bằng Python

Phần mềm hỗ trợ nhân viên và quản trị viên thực hiện các nghiệp vụ chính trong quy trình bán vé tàu:

- Quản lý thông tin ga tàu, tàu, lịch trình và toa ghế
- Tra cứu chuyến tàu theo ngày, ga đi, ga đến
- Đặt vé, bán vé, in vé và hủy vé
- Quản lý thông tin hành khách
- Theo dõi doanh thu và tình trạng chỗ ngồi

Ứng dụng dự kiến có thể phát triển bằng `Tkinter` hoặc `PyQt` trong tuần 2, và kết hợp cơ sở dữ liệu trong tuần 3.

## 2. Đối tượng sử dụng

- **Nhân viên bán vé:** tra cứu chuyến tàu, lập phiếu đặt vé, bán vé, hủy vé, tìm kiếm vé
- **Quản trị viên:** quản lý danh mục ga tàu, tàu, toa ghế, lịch trình, tài khoản và xem báo cáo

## 3. Mục tiêu hệ thống

- Giảm thời gian tìm kiếm chuyến tàu và bán vé
- Hạn chế trùng lặp hoặc bán trùng chỗ ngồi
- Quản lý dữ liệu hành khách, lịch sử đặt vé và doanh thu tập trung
- Hỗ trợ thống kê nhanh cho người quản lý

## 4. Chức năng chính

### 4.1. Đăng nhập hệ thống

- Đăng nhập bằng tên tài khoản và mật khẩu
- Phân quyền theo vai trò: nhân viên, quản trị viên
- Đăng xuất khỏi hệ thống

### 4.2. Quản lý danh mục

- Quản lý danh sách ga tàu
- Quản lý danh sách tàu
- Quản lý toa tàu và số lượng ghế theo từng toa
- Quản lý loại ghế: ghế mềm, ghế cứng, giường nằm...

### 4.3. Quản lý lịch trình

- Tạo mới lịch tàu chạy theo ngày
- Khai báo ga đi, ga đến, giờ khởi hành, giờ đến
- Gắn tàu và số hiệu chuyến tàu vào lịch trình
- Cập nhật, khóa hoặc xóa lịch trình khi cần

### 4.4. Tra cứu chuyến tàu

- Tìm chuyến tàu theo ga đi, ga đến, ngày đi
- Hiển thị thông tin:
  - mã chuyến
  - tên tàu
  - giờ khởi hành
  - giờ đến
  - số chỗ còn trống
  - giá vé theo loại ghế
- Lọc theo khung giờ hoặc loại ghế

### 4.5. Bán vé / Đặt vé

- Chọn chuyến tàu từ kết quả tra cứu
- Chọn toa và chỗ ngồi còn trống
- Nhập thông tin hành khách: họ tên, CCCD/CMND, số điện thoại
- Tính tổng tiền vé
- Xác nhận đặt vé hoặc thanh toán ngay
- Tạo mã vé duy nhất cho mỗi giao dịch

### 4.6. Quản lý vé

- Tìm kiếm vé theo mã vé, CCCD hoặc số điện thoại
- Xem chi tiết vé đã đặt
- Hủy vé theo quy định
- Cập nhật trạng thái vé: đã đặt, đã thanh toán, đã hủy
- In vé hoặc xuất thông tin vé

### 4.7. Quản lý hành khách

- Lưu thông tin hành khách đã mua vé
- Tìm kiếm lịch sử mua vé theo hành khách
- Hỗ trợ tái sử dụng dữ liệu hành khách khi mua vé lần sau

### 4.8. Báo cáo - thống kê

- Thống kê số vé đã bán theo ngày
- Thống kê doanh thu theo ngày, tháng
- Thống kê tỉ lệ lấp đầy cho từng chuyến tàu
- Liệt kê các vé đã hủy

## 5. Quy trình nghiệp vụ chính

### 5.1. Quy trình bán vé

1. Nhân viên đăng nhập hệ thống
2. Nhập ga đi, ga đến, ngày đi để tra cứu chuyến tàu
3. Chọn chuyến tàu phù hợp
4. Chọn toa và ghế còn trống
5. Nhập thông tin hành khách
6. Hệ thống tính tiền và tạo đơn đặt vé
7. Xác nhận thanh toán
8. Hệ thống cập nhật chỗ ngồi và phát hành vé

### 5.2. Quy trình hủy vé

1. Tìm vé theo mã vé hoặc thông tin hành khách
2. Kiểm tra điều kiện hủy
3. Xác nhận hủy vé
4. Hệ thống cập nhật trạng thái vé và trả lại chỗ ngồi trống

## 6. Danh sách màn hình dự kiến

- Màn hình đăng nhập
- Màn hình trang chủ / bảng điều khiển
- Màn hình tra cứu chuyến tàu
- Màn hình chọn toa - chỗ ngồi
- Màn hình lập vé / thanh toán
- Màn hình quản lý vé
- Màn hình quản lý lịch trình
- Màn hình báo cáo doanh thu

## 7. Đề xuất dữ liệu chính cho tuần 3

### 7.1. Bảng tai_khoan (tài khoản)

- ma_tai_khoan
- ten_dang_nhap
- mat_khau
- vai_tro

### 7.2. Bảng ga_tau (ga tàu)

- ma_ga
- ten_ga
- dia_diem

### 7.3. Bảng tau (tàu)

- ma_tau
- ten_tau
- so_toa

### 7.4. Bảng toa_tau (toa tàu)

- ma_toa
- ma_tau
- loai_ghe
- so_ghe

### 7.5. Bảng lich_trinh (lịch trình)

- ma_lich_trinh
- ma_tau
- ga_di
- ga_den
- ngay_di
- gio_khoi_hanh
- gio_den

### 7.6. Bảng hanh_khach (hành khách)

- ma_hanh_khach
- ho_ten
- cccd
- so_dien_thoai

### 7.7. Bảng ve_tau (vé tàu)

- ma_ve
- ma_lich_trinh
- ma_hanh_khach
- ma_toa
- so_ghe
- gia_ve
- trang_thai

## 8. Phạm vi hoàn thành trong tuần 1

- Hoàn thiện bản mô tả chức năng
- Hoàn thiện mockup cho các giao diện chính
- Sẵn sàng chuyển sang giai đoạn code frontend ở tuần 2

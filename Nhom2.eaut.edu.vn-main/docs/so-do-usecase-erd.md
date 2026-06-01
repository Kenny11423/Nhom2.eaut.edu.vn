# Sơ đồ Use Case và ERD

## 1. Sơ đồ Use Case

```mermaid
graph LR
    %% Actors
    Staff["Nhân viên bán vé"]
    Admin["Quản trị viên"]

    subgraph System ["Hệ thống quản lý bán vé tàu"]
        direction TB

        subgraph Common ["Chung"]
            Login((Đăng nhập))
            Logout((Đăng xuất))
        end

        subgraph SalesGroup ["Nhóm nghiệp vụ bán vé"]
            Search((Tra cứu chuyến tàu))
            ViewSeat((Xem ghế trống))
            Book((Đặt vé / Bán vé))
            SearchTicket((Tìm kiếm vé))
        end

        subgraph AdminGroup ["Nhóm nghiệp vụ quản trị"]
            Dashboard((Xem dashboard))
            M_Station((Quản lý ga tàu))
            M_Train((Quản lý tàu))
            M_Carriage((Quản lý toa/ghế))
            M_Schedule((Quản lý lịch trình))
            M_Account((Quản lý tài khoản))
        end

        subgraph SupportGroup ["Nghiệp vụ hỗ trợ"]
            UpdatePass((Cập nhật hành khách))
            Cancel((Hủy vé))
            Print((In / xuất vé))
        end
    end

    %% Staff associations
    Staff --> Login
    Staff --> Logout
    Staff --> Search
    Staff --> ViewSeat
    Staff --> Book
    Staff --> SearchTicket

    %% Admin associations
    Admin --> Login
    Admin --> Logout
    Admin --> Dashboard
    Admin --> M_Station
    Admin --> M_Train
    Admin --> M_Carriage
    Admin --> M_Schedule
    Admin --> M_Account

    %% Relationships
    Book -.-> |include| UpdatePass
    SearchTicket -.-> |include| UpdatePass
    SearchTicket -.-> |include| Cancel
    SearchTicket -.-> |include| Print

    %% Styling
    classDef actor fill:#f9f,stroke:#333,stroke-width:2px;
    classDef system fill:#fff,stroke:#333,stroke-width:2px;
    classDef usecase fill:#e1f5fe,stroke:#01579b,stroke-width:1px;
    
    class Staff,Admin actor;
    class Login,Logout,Search,ViewSeat,Book,SearchTicket,Dashboard,M_Station,M_Train,M_Carriage,M_Schedule,M_Account,UpdatePass,Cancel,Print usecase;
```

## 2. Sơ đồ ERD

```mermaid
erDiagram
    USERS ||--o{ TICKETS : books
    PASSENGERS ||--o{ TICKETS : owns
    TRAINS ||--o{ TRIPS : operates
    STATIONS ||--o{ STATION_TRIPS : maps
    TRIPS ||--o{ STATION_TRIPS : maps
    TRIPS ||--o{ CARRIAGE_TRIPS : assigns
    CARRIAGES ||--o{ CARRIAGE_TRIPS : participates
    CARRIAGE_TRIPS ||--o{ TRIP_SEATS : contains
    TRIPS ||--o{ TICKETS : generates
    TRIP_SEATS ||--o| TICKETS : assigned_to

    USERS {
        int id PK
        text username UK
        text password
        text full_name
        text role
    }

    STATIONS {
        int id PK
        text code UK
        text name
        text city
    }

    TRAINS {
        int id PK
        text code UK
        text name
        int carriage_count
    }

    CARRIAGES {
        int id PK
        text carriage_code
        text seat_type
        int seat_count
    }

    TRIPS {
        int id PK
        int train_id FK
        text trip_code UK
        text departure_date
        text departure_time
        text arrival_time
        float base_price
        text status
    }

    STATION_TRIPS {
        int id PK
        int trip_id FK
        int station_id FK
        int stop_order
        text arrival_time
        text departure_time
    }

    CARRIAGE_TRIPS {
        int id PK
        int trip_id FK
        int carriage_id FK
        int carriage_order
    }

    TRIP_SEATS {
        int id PK
        int carriage_trip_id FK
        text seat_code
        text seat_type
        float seat_price
        text status
    }

    PASSENGERS {
        int id PK
        text full_name
        text id_number UK
        text phone
    }

    TICKETS {
        int id PK
        text ticket_code UK
        int passenger_id FK
        int trip_id FK
        int trip_seat_id FK
        int booked_by FK
        float price
        text status
        datetime booked_at
    }
```

## 3. Ghi chú

- Sơ đồ use case bám theo mô tả ở `docs/tuan1/mo-ta-chuc-nang.md`.
- Sơ đồ ERD bên trên là phương án thiết kế đã điều chỉnh theo yêu cầu mới, chưa còn bám hoàn toàn schema hiện tại trong `src/train_ticket_app/backend/database.py`.
- Quan hệ `STATIONS - TRIPS` được biểu diễn theo N-N qua `STATION_TRIPS`, nhờ đó một chuyến từ điểm A đến điểm B có thể đi qua nhiều ga dừng trung gian theo `stop_order`.
- Quan hệ `CARRIAGES - TRIPS` được biểu diễn theo N-N qua `CARRIAGE_TRIPS`, nên toa tàu không bị cố định theo một `TRAIN` mà có thể được gán khác nhau cho từng chuyến/ngày chạy.
- Quan hệ `TRIP_SEATS` với `TICKETS` được biểu diễn là `0..1` theo mỗi ghế của một chuyến tại một thời điểm chỉ gắn với tối đa một vé đang tồn tại trong hệ thống.

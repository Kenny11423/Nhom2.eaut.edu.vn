# Phan chia cong viec tuan 2 cho 3 nguoi

Muc tieu: moi nguoi lam mot nhom file rieng de **tu commit thu cong** len Github, han che conflict.

## Nguoi 1 - Giao dien HTML/CSS/JavaScript

**Pham vi chiu trach nhiem**

- Thiet ke va chinh sua giao dien trang dang nhap
- Giao dien dashboard
- Giao dien tra cuu chuyen tau va dat ve
- Tuong tac JavaScript voi bridge

**File nen phu trach**

- `src/train_ticket_app/assets/index.html`
- `src/train_ticket_app/assets/styles.css`
- `src/train_ticket_app/assets/app.js`

**Commit goi y**

- `feat(ui): xay dung giao dien desktop html/js cho man hinh chinh`

## Nguoi 2 - Backend Python va cau noi PySide6

**Pham vi chiu trach nhiem**

- Tao cua so desktop bang `PySide6`
- Cau hinh `QWebEngineView`, `QWebChannel`
- Xu ly dang nhap
- Xu ly tra cuu chuyen tau, dat ve, huy ve
- Ket noi frontend voi backend

**File nen phu trach**

- `app.py`
- `src/train_ticket_app/main_window.py`
- `src/train_ticket_app/backend/bridge.py`

**Commit goi y**

- `feat(app): ket noi pyside6 voi frontend js qua qwebchannel`

## Nguoi 3 - Co so du lieu va du lieu mau

**Pham vi chiu trach nhiem**

- Thiet ke bang du lieu
- Tao schema SQLite
- Khoi tao du lieu mau
- Toi uu thong ke co ban bang `numpy`
- Hoan thien tai lieu thiet ke CSDL va `requirements.txt`

**File nen phu trach**

- `src/train_ticket_app/backend/database.py`
- `docs/tuan2/thiet-ke-co-so-du-lieu.md`
- `requirements.txt`
- `README.md`

**Commit goi y**

- `feat(db): thiet ke sqlite schema va seed du lieu mau`

## Cach lam de it conflict

1. Moi nguoi tao nhanh branch rieng neu can.
2. Chi sua dung nhom file duoc giao.
3. Truoc khi commit, `git pull` hoac `git fetch` va rebase neu nhom dang lam song song.
4. Commit theo tung phan nho, khong gom nhieu chuc nang vao cung mot commit.

## Thu tu commit de de ghep

1. Nguoi 3 commit schema + requirements truoc.
2. Nguoi 2 commit khung app va bridge sau.
3. Nguoi 1 commit/chinh tiep giao dien cuoi cung de can theo du lieu that.

# Project: Phan mem quan ly ban ve tau

Bo bai lam hien tai da co:

- **Tuan 1:** mo ta chuc nang va mockup giao dien
- **Tuan 2:** frontend desktop bang `PySide6 + HTML/CSS/JavaScript`, thiet ke `SQLite`, du lieu mau va bridge Python-JS

## Cau truc chinh

- [docs/tuan1/mo-ta-chuc-nang.md](docs/tuan1/mo-ta-chuc-nang.md)
- [docs/tuan1/mockup-ui.svg](docs/tuan1/mockup-ui.svg)
- [docs/tuan2/thiet-ke-co-so-du-lieu.md](docs/tuan2/thiet-ke-co-so-du-lieu.md)
- [docs/tuan2/phan-chia-cong-viec-3-nguoi.md](docs/tuan2/phan-chia-cong-viec-3-nguoi.md)
- `app.py`
- `src/train_ticket_app/`

## Thu vien can cai

Tat ca thu vien ngoai thu vien chuan da duoc khai bao trong [requirements.txt](requirements.txt):

- `PySide6`
- `numpy`

## Cach chay

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Tai khoan demo

- `admin / admin123`
- `staff / staff123`

## Ghi chu

- CSDL SQLite duoc tao tu dong tai `data/train_ticket.db`
- Frontend duoc ve bang `HTML/CSS/JS` va hien thi trong `QWebEngineView`
- `numpy` duoc dung de tinh tong doanh thu va ti le lap day trong dashboard

# 🏛️ Гишүүдийн Бүртгэл — Тохиргооны заавар

## Файл бүтэц
```
olzii_registry/
├── app.py              ← Flask сервер
├── requirements.txt    ← Flask суулгахад хэрэгтэй
├── templates/
│   └── index.html      ← Вэб хуудас
└── members.db          ← Өгөгдлийн сан (автоматаар үүснэ)
```

## VS Code дээр ажиллуулах заавар

### 1. Flask суулгах (нэг удаа)
VS Code Terminal-ийг нээгээд:
```bash
pip install flask
```

### 2. Сервер ажиллуулах
```bash
cd olzii_registry
python app.py
```

### 3. Браузерт нээх
```
http://localhost:5000
```

## Зогсоох
Terminal дээр `Ctrl + C` дарна.

## Тэмдэглэл
- Мэдээлэл `members.db` файлд хадгалагдана
- Файл устгавал бүх мэдээлэл устана — нөөцлөлтийг мартуузай

# Hotel booking · P03–P06

P03, P04, P05 va P06 materiallari asosida yig‘ilgan yakuniy Python loyihasi.
Barcha joriy kod va hujjatlar shu papkada. Ishga tushirish uchun boshqa dars
papkalariga murojaat qilinmaydi. Python 3.11 yoki yangiroq versiya kerak.

## Ishga tushirish

Terminalni `hotel-booking/` papkasida oching:

```sh
python -m unittest -v
python main.py
python main.py --race
```

Ilova va uning 8 ta testi faqat Python standart kutubxonasidan foydalanadi.
Modullar chegaralarini tekshiruvchi vositani bir marta o‘rnating:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
lint-imports --no-cache
```

Windows PowerShell uchun faollashtirish: `.venv\Scripts\Activate.ps1`.

## Papka tarkibi

```text
hotel-booking/
├── docs/
│   ├── requirements.md
│   ├── design-notes.md
│   ├── quality-scenarios.md
│   ├── contexts.md
│   ├── adr-001-modular-monolith.md
│   └── diagrams.drawio
├── hotel_booking/
│   ├── __init__.py
│   ├── rooms/           # Room, RoomCatalog; internal.py
│   ├── reservations/    # BookingService, domain, store contract; internal.py
│   ├── payments/        # PaymentService, PaymentStatus; internal.py
│   └── notifications/   # Confirmation, NotificationSender; internal.py
├── main.py
├── test_booking_service.py
├── pyproject.toml
└── requirements-dev.txt
```

`main.py` obyektlarni yig‘adi. Moduldan tashqaridagi ilova kodi faqat shu faylda
`internal.py` klasslarini tanlaydi; testlar ham ulardan foydalanishi mumkin.
Payments alohida shartnoma va simulyatsiyaga ega, lekin bron qilish oqimiga hali
ulanmagan. Demo haqiqiy to‘lov olmaydi, email yoki SMS jo‘natmaydi.

## P05 · Bajarilgan vazifalar

| Qadam | Natija |
|---|---|
| 1. Stakeholder va S1–S6 | [O‘lchanadigan sifat ssenariylari](docs/quality-scenarios.md) |
| 2. Mehmonxona atamalari | [Words](docs/contexts.md#words) |
| 3. To‘rtta kontekst | [Four contexts](docs/contexts.md#four-contexts) |
| 4. Bir so‘zning turli ma’nolari | [Same word, different meaning](docs/contexts.md#same-word-different-meaning) |
| 5. Sakkizta qoida egasi | [Rule owners](docs/contexts.md#rule-owners) |
| 6. Kontekst xaritasi | `docs/diagrams.drawio` → **Context map** |
| 7. Chegaradan o‘tuvchi ma’lumotlar | [Between contexts](docs/contexts.md#between-contexts) |
| 8. Tekshirish va topshirish | Ushbu papka va quyidagi P06 natijalari |

## P06 · Bajarilgan vazifalar

| Qadam | Natija |
|---|---|
| 1. Boshlang‘ich holat | P04: 8 ta test, 9 qator demo, ikki bronli race tekshirildi |
| 2. Modul papkalari | Rooms, Reservations, Payments, Notifications |
| 3. Rooms va Notifications | RoomCatalog va mustaqil Confirmation xabari |
| 4. Reservations va Payments | BookingService, store, PaymentService va SimulatedPaymentService |
| 5. Wiring | `main.py` katalog, store va senderni tanlaydi |
| 6. Arxitektura tekshiruvlari | `pyproject.toml`: 3 ta kontrakt |
| 7. Ataylab buzib ko‘rish | Taqiqlangan import tekshiruvni yiqitdi; import olib tashlandi |
| 8. Yakuniy tekshiruv va qaror | 8 ta test; o‘sha demo va race; ADR-001; **Modules** diagrammasi |

Tekshiruv dalillari va 7-qadamni takrorlash tartibi:
[P06 design notes](docs/design-notes.md#p06-design-notes).

## Kutilgan demo

```text
Free rooms 12-14 Nov: R7, R8
Maya books R7 12-14 Nov: Accepted R101
Omar books R7 13-15 Nov: Unavailable
Nora books R7 14-16 Nov: Accepted R102
Omar books R8 15-15 Nov: InvalidDates
Free rooms 12-14 Nov: R8
Maya cancels R101: True
Free rooms 12-14 Nov: R7, R8
Confirmation emails sent: 2
```

Race topshiriqqa ko‘ra saqlangan: `--race` R7 uchun ikkita `Confirmed` bron va
`Double booking!` xabarini ko‘rsatadi. P06 faqat tuzilmani o‘zgartiradi; bu
parallel bron qilish xatosini P09 da tuzatish rejalashtirilgan.

## Manbalar qanday birlashtirildi

| Manba | Yakuniy loyihadagi o‘rni |
|---|---|
| `p03/hotel-booking/docs/` | R1–R5, dastlabki design notes va **Use cases** sahifasi saqlandi |
| `p04/` | 8 ta test va demo/race xulqi boshlang‘ich mezon sifatida olindi |
| `p04/docs/` | P05 kontekst va sifat hujjatlari to‘ldirildi, **Context map** qo‘shildi |
| `p06/` | To‘rtta modul kodi, 8 ta moslashtirilgan test va ADR asos qilib olindi |

P03 faylida R6 yo‘q edi; u P04 kodi va testlarida mavjud confirmation qoidasidan
tiklandi. P03 design notes matni boshida saqlandi, keyin P04/P06 bo‘limlari
qo‘shildi. Eski `Step2` testlari P03 dagi `EmailSender` va konkret
`ReservationStore` nomlarini ishlatadi; yakuniy test to‘plami ularning o‘rnini
bosgan P04/P06 dagi 8 ta testdan iborat.

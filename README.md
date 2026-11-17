# Pixel-Pattern One Page Summary Generator

Generator PDF "One Page Summary" bergaya **pixel pattern / modular tile design**
dari file konten riset (JSON). Konten riset contoh: *10 Market Leader Software
POS di Indonesia*.

## Preview

| Halaman 1 | Halaman 2 |
|---|---|
| Header + Executive Summary + Key Findings | Key Insights + motif tile |

Jalankan `python build.py` lalu buka `output/summary.pdf` (6 halaman, US Letter).

## Cara pakai

```bash
# 1. (opsional) buat virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 2. install dependensi
pip install -r requirements.txt

# 3. generate PDF
python build.py
```

Output: `output/summary.pdf` — tepat **6 halaman** (divalidasi otomatis oleh script).

## Ganti konten

Semua isi laporan dipisah ke [`content.json`](content.json):

- `meta` - judul, subjudul, penulis, tanggal, chip header
- `executive_summary` - paragraf ringkasan (kata kunci otomatis di-highlight marker kuning)
- `key_findings` - 6 temuan
- `key_insights` - 3 kartu insight (`color`: blue/red/green)
- `top10` - kartu ranking 1-10 (`tier`: MARKET LEADER / STRONG / ENTERPRISE / VALUE / NICHE)
- `comparison_table` - header, 10 baris, footnote
- `recommendation` - pilihan utama + rekomendasi per kebutuhan
- `sources` - 15 sumber (2 kolom)

## Ganti palet warna

Edit konstanta di bagian atas `build.py`:

```python
BLUE   = HexColor("#2347E8")
YELLOW = HexColor("#FFD21F")
RED    = HexColor("#E9372B")
# ...dst
```

## Desain

- **Motif tile**: kotak grid 5x5 simetris (mirror horizontal & vertikal) dari
  seed acak deterministik (`hashlib.md5`) - warna dari palet, border hitam 1.2pt
- Kartu border hitam 1.6pt, sudut siku, bayangan solid offset 5pt
- Strip pixel acak di tepi atas & bawah tiap halaman
- Font: Poppins (Regular/SemiBold/Bold) + DejaVu Sans (simbol →/✓), keduanya lisensi OFL - lihat `fonts/`

## Struktur

```
├── build.py          # script utama (reportlab, canvas-based)
├── content.json      # seluruh konten riset (dipisah dari tampilan)
├── fonts/            # Poppins .ttf + DejaVu Sans (OFL)
├── output/           # summary.pdf dihasilkan di sini
├── requirements.txt
└── README.md
```

## Lisensi

MIT - lihat [LICENSE](LICENSE). Font di `fonts/` berlisensi OFL masing-masing.

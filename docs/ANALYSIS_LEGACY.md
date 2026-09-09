# Analisis lengkap Mod-main lama

Dokumen ini merangkum audit terhadap source code pada arsip Mod-main lama dan membandingkannya dengan
alur pada dokumen pendukung `Joki (1).pdf` serta `Analisis Lengkap Seluruh kode.pdf`.

## 1. Gambaran source lama

Arsip lama berisi lima aplikasi Tkinter terpisah dan satu menu launcher sederhana:

- `Auto_Login/auto_login_persistent.py`
- `Auto_Quest_Individual/auto_quest_individual.py`
- `Auto_Quest_Mysteriland/auto_quest_mysteriland.py`
- `Auto_Quest_Supremacy/auto_quest_supremacy.py`
- `Auto_War/auto_war.py`
- `main_menu.py`

Fungsi dasar sudah ada: konfigurasi koordinat, background thread, logging ke GUI, klik dengan
PyAutoGUI, quest loops, OCR untuk Auto War, dan penyimpanan JSON. Namun, masing-masing modul
mengimplementasikan pola yang sama sendiri-sendiri sehingga behavior, error handling, format config,
dan mekanisme Stop menjadi tidak konsisten.

## 2. Temuan kritis

### 2.1 Kredensial plaintext di source tree

Arsip lama mengandung file akun dengan alamat akun dan password plaintext. File semacam ini tidak
boleh ikut ke GitHub. Versi 2.0 tidak menyalin file tersebut, `.gitignore` memblokir pola akun umum,
dan GUI Auto Login sengaja tidak menyimpan editor akun ketika tombol **Save Profile** digunakan.

Jika kredensial tersebut nyata, lakukan rotasi password. Jika pernah masuk ke Git, hapus juga dari
history; menghapus file di commit terbaru saja tidak menghilangkan secret dari commit lama.

### 2.2 Path absolut milik satu komputer

Auto War lama memuat path konfigurasi yang mengarah ke direktori user Windows tertentu. Auto Login
juga bergantung pada path browser yang hardcoded. Ini membuat repository tidak portable dan juga
membocorkan struktur lokal mesin pengembang.

Versi 2.0 menggunakan `platformdirs` untuk user config/log dan menjadikan executable browser,
Tesseract, Sandboxie, serta game sebagai konfigurasi.

### 2.3 Bug runtime `sys` pada Auto War

Source Auto War lama menggunakan `sys` untuk menentukan resource path, tetapi tidak mengimpor
`sys` pada bagian import. Ini dapat menghasilkan `NameError` saat startup walaupun `compileall`
tidak selalu mendeteksi masalah nama runtime.

### 2.4 Salah API keyboard

Source lama memanggil pola `pyautogui.key('delete')`. PyAutoGUI menggunakan `press()` untuk tombol
keyboard. Selain itu, triple-click + delete rapuh untuk field search. Versi 2.0 memusatkan operasi
clear field menjadi klik → `Ctrl+A` → `Backspace`.

### 2.5 Off-by-one pada March target

Flow lama menggunakan variabel `Q` dengan semantik 1-based, lalu menambah satu dan menggunakannya
langsung sebagai index Python. Akibatnya target berikutnya dapat melompat satu kota. Versi 2.0
menggunakan `MarchState.current_index` 0-based dan `next_city()` sehingga target berikutnya adalah
route index yang benar.

### 2.6 Update Tkinter dari worker thread

Beberapa script lama langsung mengubah widget Tkinter, progress bar, atau membuka messagebox dari
thread automation. Tkinter tidak thread-safe; `update_idletasks()` tidak mengubah fakta tersebut.
Ini dapat menimbulkan freeze atau `TclError` yang sulit direproduksi.

Versi 2.0 menggunakan queue `UiBus`. Worker hanya menulis event ke queue, dan main Tk thread yang
mengubah widget melalui polling `after()`.

### 2.7 Stop tidak responsif

Banyak `time.sleep()` panjang di source lama. Mengubah flag `running` tidak memutus sleep yang sedang
berlangsung, sehingga tombol Stop terlihat tidak bekerja sampai sleep selesai. Versi 2.0 memakai
`StopToken` berbasis `threading.Event`; seluruh wait utama bersifat interruptible.

### 2.8 Model threading multi-instance tidak aman bila diterapkan mentah

Dokumen desain meminta thread independen per Sandboxie instance. Namun PyAutoGUI mengendalikan satu
mouse/keyboard OS yang global. Jika dua thread melakukan click bersamaan, fokus dan koordinat dapat
tercampur walaupun window handle berbeda.

Versi 2.0 tetap memakai worker pool untuk state/flow per instance, tetapi **focus + transform + click**
dilindungi satu shared `RLock`. Jadi instance tetap dikelola secara concurrent tanpa membuat dua
thread berebut input fisik.

### 2.9 Main menu lama hanya cocok untuk hasil paket tertentu

`main_menu.py` lama mengasumsikan sub-aplikasi sudah berupa `.exe` relatif terhadap executable
launcher. Saat repository dijalankan sebagai source, asumsi ini tidak valid. Versi 2.0 menggunakan
satu package dan satu entry point: `python -m wotk` / `wotk-mod`.

### 2.10 Tesseract dibundel sebagai binary besar

Arsip lama menyertakan folder Tesseract beserta EXE/DLL. Ini membengkakkan repository dan
mencampurkan source project dengan distribusi pihak ketiga. Versi 2.0 mendeteksi Tesseract dari:

1. path eksplisit di config,
2. environment variable `WOTK_TESSERACT_CMD`,
3. `PATH`,
4. lokasi Windows standar.

Binary Tesseract tidak ikut di ZIP final.

## 3. Analisis per modul

### Auto Login

**Yang sudah benar di versi lama**

- punya model data akun;
- punya flow login/register;
- dapat membuka browser, mengganti tab, logout, dan memilih server;
- ada GUI coordinate setup dan status logging.

**Masalah utama**

- credential persistence tidak aman;
- browser path machine-specific;
- tidak ada explicit cooperative Stop;
- window focus bergantung pada pencarian title sederhana;
- logic input/click diduplikasi dari modul lain.

**Perbaikan 2.0**

- `LoginEngine` memisahkan automation dari GUI;
- account secrets hanya berada di editor memory;
- settings dan coordinates boleh disimpan, account editor tidak ikut disimpan;
- browser/path/window pattern configurable;
- semua click/write/hotkey melalui `AutomationContext` dan `StopToken`.

### Auto Quest Individual

**Flow dipertahankan**

`Challenge → Crusade → Individual → Stage N → Fight → Quick Combat → OK → Reward N → Claim`.

**Perbaikan**

- validasi stage 1–10;
- validasi semua coordinate yang diperlukan sebelum mulai;
- delay dibuat dataclass tervalidasi;
- Stop dapat memutus delay;
- reset dan exit menjadi method eksplisit.

### Auto Quest Mysteriland

**Flow dipertahankan**

`Challenge → Crusade → Mysteriland`, kemudian stage 1–5 menjalankan
`Stage → Enter Challenge → Fight → Quick Combat → OK → Reward`.

Fitur swipe 1x/5x tetap ada. Karena dokumen menunjukkan konfigurasi stage dapat berbeda berdasarkan
hari, GUI 2.0 menyimpan satu profile lengkap; user dapat memakai profile berbeda per hari bila
koordinat stage memang berbeda.

### Auto Quest Supremacy

Source lama mendefinisikan:

- maksimum loop;
- jumlah loop fase awal;
- 8 hero;
- maksimum penggunaan hero;
- 12 challenge.

Tetapi implementasi rotasi hero lama tidak benar-benar memanfaatkan seluruh konfigurasi tersebut
secara konsisten. Pada fase kedua, subset hero dapat cepat habis walaupun `max_hero_usage` masih
mengizinkan reuse.

Versi 2.0 memilih hero dengan usage paling kecil, menambah counter setiap penggunaan, dan membatasi
pemilihan sesuai `heroes_per_battle` dan `max_hero_usage`. Ketika semua hero mencapai cap pada run
yang panjang, counter di-reset sebagai rotasi baru dengan log eksplisit.

Challenge 7–12 tetap menggunakan scroll dan slot 1–6 sebagaimana pola source lama.

### Auto War

Ini modul paling kompleks dan paling membutuhkan restrukturisasi.

**Flow inti lama**

- multi-account via `Ctrl+Tab`;
- target berdasarkan warna kota;
- Search → nama kota → Fight → Dispatch → Minimize;
- OCR dan color detection;
- loop panjang sampai dihentikan atau target tercapai.

**Flow terbaru dari dokumen pendukung yang diterapkan 2.0**

1. klik current city setelah Minimize;
2. OCR cek `Watch`;
3. jika ada, klik Watch lalu March;
4. jika OCR menemukan `No hero can march`, klik Back dan hentikan chain akun itu;
5. jika prompt `Please Select the city you want to visit` muncul, ambil target berikutnya;
6. search target Assault;
7. optional OCR `Assault`, optional click Assault/Confirm;
8. jika berhasil, target baru dianggap current city dan Watch/March diperiksa lagi;
9. chain dibatasi `max_march_hops`;
10. setelah akun selesai, `Ctrl+Tab` ke akun berikutnya;
11. cycle timer default 31 menit dan periodic March check tersedia.

`Defender` tetap bisa dikonfigurasi sebagai OCR area untuk observability, tetapi bukan dipakai sebagai
satu-satunya state machine karena dokumen revisi terakhir lebih berfokus pada Watch/March/Assault.

### Multi-instance Sandboxie

Versi 2.0 mengimplementasikan komponen yang sebelumnya hanya berupa spesifikasi:

- load `master_config.json` dan seluruh instance JSON;
- optional launch game di **existing** Sandboxie box;
- window title/index mapping;
- client-relative coordinate transformation;
- optional offset correction;
- expected client-size warning;
- focus before each click;
- mode Individual/Supremacy/Mysteriland per instance;
- thread pool;
- global emergency hotkey best-effort;
- stop propagation antar worker bila satu instance gagal;
- serialization input fisik.

Sengaja **tidak** membuat atau mengubah Sandboxie isolation/resource policy secara otomatis. Operasi
itu memiliki konsekuensi keamanan dan lebih aman dilakukan oleh user di Sandboxie-Plus sebelum run.

## 4. Perbaikan repository/GitHub

Versi lama praktis tidak memiliki README teknis yang cukup, dependency pinning yang konsisten,
tests, CI, security policy, migration guide, atau build script terpusat. Versi 2.0 menambahkan:

- `pyproject.toml`;
- root requirements;
- `.gitignore` yang memblokir secret/local calibration/binary besar;
- README lengkap;
- SECURITY, CONTRIBUTING, CHANGELOG;
- sanitized config examples;
- unit tests dengan `RecordingBackend`;
- GitHub Actions;
- setup verifier;
- Windows build script;
- migration helper;
- dokumentasi traceability dan validation.

## 5. Batasan yang masih membutuhkan konfigurasi lokal

Tidak ada source code yang dapat mengetahui koordinat game yang benar untuk semua komputer tanpa
kalibrasi. Contoh final sengaja berisi `0,0`. Selain itu, integrasi berikut tetap harus diverifikasi
di Windows pengguna:

- title UC Browser aktual;
- lokasi executable browser;
- Tesseract OCR terpasang;
- Sandboxie box dan path game;
- DPI scaling/resolusi/window client area;
- semua coordinate dan OCR region;
- variasi bahasa/teks UI game;
- timing jaringan pada account/game yang nyata.

Karena itu, `versi jadi` di sini berarti source repository lengkap, konsisten, dapat di-install,
dapat diuji secara deterministik, dan siap dikalibrasi — bukan berarti koordinat untuk perangkat
pengguna dapat ditebak atau divalidasi tanpa menjalankan game di perangkat tersebut.

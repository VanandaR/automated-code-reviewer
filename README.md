# Asisten System Analyst AI

## 1. Tentang Proyek

Asisten System Analyst AI adalah sebuah aplikasi Command-Line Interface (CLI) yang dirancang untuk mengotomatisasi proses tinjauan kode awal (*preliminary code review*).

Aplikasi ini bekerja dengan mengambil *link Merge Request* (MR) dari sebuah tiket Jira, menganalisis perubahan kode menggunakan model AI (seperti GPT dari OpenAI), dan mem-posting hasilnya sebagai komentar terstruktur kembali ke tiket Jira tersebut.

## 2. Tumpukan Teknologi

-   **Bahasa:** Python 3.10+
-   **Pustaka Utama:**
    -   `requests`: Klien HTTP
    -   `jira-python`: Interaksi dengan Jira API
    -   `python-gitlab`: Interaksi dengan GitLab API
    -   `google-generativeai`: Interaksi dengan Google Gemini API
    -   `python-dotenv`: Manajemen variabel lingkungan

## 3. Instalasi dan Setup

### Langkah 1: Clone Repositori

```bash
git clone <URL_REPOSITORI_ANDA>
cd sa_automation
```

### Langkah 2: Buat dan Aktifkan Virtual Environment (Direkomendasikan)

```bash
# Untuk Windows
python -m venv venv
venv\Scripts\activate

# Untuk macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Langkah 3: Instal Dependensi

Pastikan Anda berada di direktori utama proyek, lalu jalankan:
```bash
pip install -r requirements.txt
```

## 4. Konfigurasi

Sebelum menjalankan aplikasi, Anda perlu menyediakan kredensial untuk layanan yang digunakan.

1.  Salin file contoh `.env.example` menjadi file `.env`.
    ```bash
    # Untuk Windows
    copy .env.example .env

    # Untuk macOS/Linux
    cp .env.example .env
    ```

2.  Buka file `.env` dan isi semua variabel yang diperlukan:
    -   `JIRA_SERVER`: URL instance Jira Anda (misal: `https://namaanda.atlassian.net`).
    -   `JIRA_USERNAME`: Email yang Anda gunakan untuk login Jira.
    -   `JIRA_PAT`: Personal Access Token yang Anda buat dari dalam profil Jira Anda (biasanya untuk Jira Server/Data Center).
    -   `GITLAB_SERVER`: URL instance GitLab Anda (misal: `https://gitlab.com`).
    -   `GITLAB_PRIVATE_TOKEN`: Personal Access Token GitLab dengan scope `api`.
    -   `GEMINI_API_KEY`: API Key dari Google AI Studio. Anda bisa mendapatkannya dari [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

Aplikasi ini akan secara otomatis mendeteksi proyek GitLab dari URL Merge Request, sehingga Anda tidak perlu mengatur Project ID secara manual.

## 5. Cara Menjalankan Aplikasi

Untuk memulai analisis, jalankan `main.py` dari terminal dengan argumen `--ticket` diikuti oleh ID tiket Jira yang ingin dianalisis.

**Contoh:**
```bash
python main.py --ticket "PROJ-123"
```

Aplikasi akan menjalankan alur kerja dan menampilkan log proses di terminal. Jika berhasil, sebuah komentar baru akan muncul di tiket Jira `PROJ-123`.
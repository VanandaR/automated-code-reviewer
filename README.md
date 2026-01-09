# Asisten System Analyst AI

## 1. Tentang Proyek

Asisten System Analyst AI adalah sebuah aplikasi Command-Line Interface (CLI) yang dirancang untuk mengotomatisasi proses tinjauan kode awal (*preliminary code review*).

Aplikasi ini bekerja dengan mengekstrak link *Merge Request* (MR) atau *Commit* dari sebuah tiket Jira, menganalisis perubahan kode menggunakan model AI canggih (melalui OpenRouter), dan mem-posting hasilnya sebagai komentar yang terstruktur dan dapat ditindaklanjuti kembali ke tiket Jira tersebut.

## 2. Fitur Utama

-   **Analisis Multi-Bahasa**: Secara otomatis mendeteksi bahasa (misalnya, Java, React) dalam *diff* dan menerapkan praktik terbaik yang relevan.
-   **Umpan Balik Dapat Ditindaklanjuti**: Memberikan rekomendasi perbaikan konkret dengan contoh kode yang siap disalin-tempel.
-   **Rekomendasi Otomatis**: Secara otomatis menyarankan "Naik Staging" atau "Revisi" berdasarkan hasil analisis.
-   **Format Komentar yang Disesuaikan**: Menghasilkan komentar Jira yang bersih, ringkas, dan dirancang untuk programmer.
-   **Dukungan OpenRouter**: Terintegrasi dengan OpenRouter untuk fleksibilitas model AI dan untuk memanfaatkan model gratis atau berbayar.

## 3. Tumpukan Teknologi

-   **Bahasa:** Python 3.10+
-   **Pustaka Utama:**
    -   `requests`: Klien HTTP
    -   `jira-python`: Interaksi dengan Jira API
    -   `python-gitlab`: Interaksi dengan GitLab API
    -   `openai`: Interaksi dengan API yang kompatibel dengan OpenAI (termasuk OpenRouter)
    -   `python-dotenv`: Manajemen variabel lingkungan

## 4. Instalasi dan Setup

### Langkah 1: Clone Repositori

```bash
git clone <URL_REPOSITORI_ANDA>
cd <NAMA_DIREKTORI_PROYEK>
```

### Langkah 2: Buat dan Aktifkan Virtual Environment

```bash
# Untuk Windows
python -m venv .venv
.venv\Scripts\activate

# Untuk macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Langkah 3: Instal Dependensi

```bash
pip install -r requirements.txt
```

## 5. Konfigurasi

1.  Salin file contoh `.env.example` menjadi file `.env`.
    ```bash
    # Untuk Windows
    copy .env.example .env

    # Untuk macOS/Linux
    cp .env.example .env
    ```

2.  Buka file `.env` dan isi semua variabel yang diperlukan:
    -   `JIRA_SERVER`: URL instance Jira Anda.
    -   `JIRA_PAT`: Personal Access Token Jira Anda.
    -   `GITLAB_SERVER`: URL instance GitLab Anda.
    -   `GITLAB_PRIVATE_TOKEN`: Personal Access Token GitLab dengan scope `api`.
    -   `AI_SERVICE_PROVIDER`: Diatur ke `openai` secara default.
    -   `OPENAI_API_KEY`: Kunci API OpenRouter Anda (misalnya, `sk-or-v1-...`).
    -   `OPENAI_BASE_URL`: URL dasar API OpenRouter (`https://openrouter.ai/api/v1`).

## 6. Cara Menjalankan Aplikasi

Jalankan `main.py` dari terminal dengan argumen `--ticket` diikuti oleh ID tiket Jira.

**Contoh:**
```bash
python main.py --ticket "PROJ-123"
```

Aplikasi akan menggunakan `openai` (dikonfigurasi untuk OpenRouter) secara default. Jika Anda ingin menggunakan penyedia lain (misalnya, `gemini`), Anda dapat menentukannya dengan *flag* `--ai-provider`.

**Contoh dengan penyedia yang berbeda:**
```bash
python main.py --ticket "PROJ-123" --ai-provider gemini
```

Aplikasi akan menjalankan alur kerja dan menampilkan log proses di terminal. Jika berhasil, sebuah komentar baru akan muncul di tiket Jira yang ditentukan.
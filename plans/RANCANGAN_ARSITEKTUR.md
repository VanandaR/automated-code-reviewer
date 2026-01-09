# Rancangan Arsitektur & Teknis: Asisten System Analyst AI (Versi CLI)

Dokumen ini menguraikan arsitektur teknis, tumpukan teknologi, dan rencana implementasi untuk aplikasi "Asisten System Analyst AI" versi Command-Line Interface (CLI).

## 1. Visi & Lingkup Proyek (Versi CLI)

Aplikasi ini bertujuan untuk mengotomatisasi proses *preliminary code review* dengan cara menjalankan sebuah skrip dari terminal. Pengguna akan memasukkan ID Tiket Jira sebagai input, dan aplikasi akan melakukan analisis kode dari *merge request* yang tertaut, kemudian mempublikasikan hasilnya sebagai komentar di tiket Jira tersebut.

**Alur Kerja Utama:**
1.  Pengguna menjalankan aplikasi dari terminal: `python main.py --ticket JIRA-123`
2.  Aplikasi mengambil detail tiket `JIRA-123` dari Jira.
3.  Aplikasi mengekstrak URL *Merge Request* (MR) GitLab dari deskripsi tiket.
4.  Aplikasi mengambil *code diff* dari MR tersebut menggunakan API GitLab.
5.  Aplikasi mengirimkan *code diff* ke model AI (LLM) untuk dianalisis.
6.  Aplikasi menerima hasil analisis dari LLM.
7.  Aplikasi memformat hasil analisis menjadi komentar yang terstruktur.
8.  Aplikasi mem-posting komentar tersebut ke tiket `JIRA-123` dan me-mention developer terkait.

## 2. Desain Arsitektur

Karena ini adalah aplikasi CLI, arsitekturnya sederhana dan berbasis modul.

```mermaid
graph TD
    A[User Terminal] -->|1. Jalankan `main.py --ticket JIRA-123`| B(main.py - CLI Handler);
    B -->|2. Panggil JiraService| C(services/jira_service.py);
    C -->|3. GET /rest/api/2/issue/{ticketId}| D[Jira API];
    D -->|4. Detail Tiket (termasuk URL MR)| C;
    C -->|5. Kembalikan URL MR| B;
    B -->|6. Panggil GitLabService| E(services/gitlab_service.py);
    E -->|7. GET /api/v4/projects/{...}/merge_requests/{...}/changes| F[GitLab API];
    F -->|8. Code Diff| E;
    E -->|9. Kembalikan Code Diff| B;
    B -->|10. Panggil AIService| G(services/ai_service.py);
    G -->|11. Kirim Prompt + Code Diff| H[LLM API - e.g., OpenAI/Claude];
    H -->|12. Hasil Analisis (JSON/Text)| G;
    G -->|13. Kembalikan Hasil Analisis| B;
    B -->|14. Panggil JiraService untuk post comment| C;
    C -->|15. POST /rest/api/2/issue/{ticketId}/comment| D;
    D -->|16. Sukses/Gagal| C;
    C -->|17. Kembalikan status| B;
    B -->|18. Tampilkan pesan sukses di terminal| A;

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
    style E fill:#ccf,stroke:#333,stroke-width:2px
    style G fill:#ccf,stroke:#333,stroke-width:2px
```

## 3. Rekomendasi Tumpukan Teknologi

-   **Bahasa Pemrograman:** **Python 3.10+**
    -   *Alasan:* Ekosistem yang matang untuk interaksi API, skrip, dan AI/ML. Pustaka yang tersedia sangat lengkap dan komunitasnya besar.

-   **Pustaka Kunci:**
    -   **Manajemen CLI:** `argparse` (bawaan Python) atau `typer` untuk antarmuka yang lebih modern.
    -   **Interaksi API (HTTP Client):** `requests` - Standar industri, sederhana dan andal.
    -   **Konektor Jira:** `jira-python` - Pustaka resmi yang menyederhanakan interaksi dengan Jira API.
    -   **Konektor GitLab:** `python-gitlab` - Pustaka komprehensif untuk GitLab API.
    -   **Konektor LLM:** Tergantung pada model yang dipilih.
        -   `openai` untuk model GPT.
        -   `anthropic` untuk model Claude.
    -   **Manajemen Konfigurasi & Secret:** `python-dotenv` - Untuk memuat variabel lingkungan (API keys, tokens) dari file `.env`.
    -   **Manajemen Dependensi:** `pip` dengan file `requirements.txt`.

## 4. Struktur Proyek yang Direkomendasikan

```
sa_automation/
|
├── .env                 # Menyimpan semua kredensial (JIRA_URL, JIRA_TOKEN, etc.)
├── .gitignore           # Mengabaikan file yang tidak perlu (seperti .env, __pycache__)
├── main.py              # Titik masuk utama aplikasi CLI
├── requirements.txt     # Daftar dependensi Python
|
├── config/
│   └── __init__.py
│   └── settings.py      # Memuat konfigurasi dari .env
|
├── services/
│   ├── __init__.py
│   ├── jira_service.py    # Logika untuk berinteraksi dengan Jira
│   ├── gitlab_service.py  # Logika untuk berinteraksi dengan GitLab
│   └── ai_service.py      # Logika untuk mengirim data ke LLM dan memproses hasilnya
|
└── prompts/
    └── code_review_prompt.txt # Template prompt untuk analisis kode
```

## 5. Pertimbangan Keamanan

-   **Kredensial:** Semua token (Jira, GitLab, AI) **HARUS** disimpan dalam file `.env` dan tidak boleh di-commit ke repositori Git. File `.env` harus ada di dalam `.gitignore`.
-   **Validasi Input:** Lakukan validasi dasar pada ID tiket Jira untuk mencegah input yang tidak valid.
-   **Error Handling:** Implementasikan blok `try...except` yang kuat di setiap panggilan API untuk menangani kegagalan koneksi, otentikasi yang salah, atau respons API yang tidak terduga.

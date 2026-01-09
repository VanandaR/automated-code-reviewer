# Solusi Alternatif Mekanisme Pengambilan Perbedaan (Diff Fetching)

## 1. Latar Belakang Masalah

Mekanisme pengambilan perbedaan (diff fetching) yang ada, yang sepenuhnya mengandalkan GitLab API melalui `gitlab_service.py`, dilaporkan sepenuhnya tidak berfungsi. Hal ini dapat disebabkan oleh berbagai faktor, seperti keterbatasan API, masalah konektivitas jaringan, atau pembatasan rate limit dari GitLab itu sendiri. Ketergantungan tunggal pada API ini menyebabkan kerentanan dan ketidakandalan dalam proses tinjauan kode otomatis.

## 2. Desain Solusi Alternatif

Untuk mengatasi masalah ini, telah dirancang solusi alternatif yang tangguh dengan memperkenalkan `GitService` baru yang akan menangani operasi Git lokal. Solusi ini bertujuan untuk:

*   **Keandalan:** Menyediakan mekanisme fallback jika pengambilan diff dari GitLab API gagal.
*   **Efisiensi:** Berpotensi mengurangi beban pada GitLab API dan memanfaatkan kecepatan operasi Git lokal.
*   **Akurasi:** Memastikan diff yang diambil konsisten, baik dari sumber lokal maupun API.

### Komponen Utama:

1.  **`GitService` (services/git_service.py):**
    *   Bertanggung jawab untuk mengkloning repositori secara lokal ke direktori sementara (`temp_repos`).
    *   Mampu mengambil perbedaan commit menggunakan perintah `git show <commit_sha> --patch`.
    *   Mengelola siklus hidup repositori lokal (kloning, pull, dan pembersihan).
    *   Dapat mengurai URL repositori dari URL commit atau MR GitLab untuk membentuk URL clone yang benar.

2.  **`DiffFetcher` (main.py):**
    *   Kelas ini dimodifikasi untuk mengorkestrasi pengambilan diff.
    *   Ketika diminta untuk mengambil diff commit, `DiffFetcher` akan *mencoba* menggunakan `GitService` lokal terlebih dahulu.
    *   Jika pengambilan diff lokal berhasil, itu akan mengembalikan hasilnya.
    *   Jika pengambilan diff lokal gagal (misalnya, repositori tidak dapat dikloning, commit tidak ditemukan secara lokal, atau ada kesalahan git), maka `DiffFetcher` akan *kembali* menggunakan `GitLabService` (API GitLab) sebagai mekanisme fallback.
    *   Untuk *Merge Request (MR)*, `DiffFetcher` akan tetap sepenuhnya mengandalkan `GitLabService` karena konsep MR secara inheren merupakan fitur tingkat platform dan tidak ada padanan langsung dalam operasi Git lokal murni.

### Alur Kerja:

1.  Aplikasi menerima URL GitLab (commit atau MR).
2.  Jika URL adalah MR, `DiffFetcher` memanggil `GitLabService.get_merge_request_diff()`.
3.  Jika URL adalah commit:
    *   `DiffFetcher` mengurai project path dan commit SHA dari URL.
    *   `DiffFetcher` mencoba mengkloning repositori yang relevan secara lokal menggunakan `GitService.clone_repository()`. Jika repositori sudah ada, ia akan melakukan `git pull`.
    *   `DiffFetcher` kemudian mencoba mengambil diff commit secara lokal menggunakan `GitService.get_commit_diff()`.
    *   Jika langkah-langkah lokal berhasil, diff dikembalikan.
    *   Jika salah satu langkah lokal gagal, `DiffFetcher` akan fallback dengan memanggil `GitLabService.get_commit_diff()`.

## 3. Implementasi

Perubahan diimplementasikan di file-file berikut:

*   **`services/git_service.py` (Baru):**
    *   Mencakup kelas `GitService` dengan metode untuk `_execute_git_command`, `_get_repo_name_from_url`, `clone_repository`, `get_commit_diff`, dan `cleanup_temp_repos`.
    *   Menggunakan `subprocess` untuk menjalankan perintah `git` CLI.
    *   Membuat direktori `temp_repos` untuk kloning lokal.

*   **`main.py` (Modifikasi):**
    *   `DiffFetcher` diinisialisasi dengan `GitService` selain `GitLabService`.
    *   Metode `fetch_commit_diff` di `DiffFetcher` diperbarui untuk menerapkan logika fallback: mencoba lokal terlebih dahulu, lalu ke API GitLab.
    *   Import `urlparse` ditambahkan untuk fungsionalitas penguraian URL.

*   **`config/settings.py` (Modifikasi):**
    *   Menambahkan variabel konfigurasi `LOCAL_GIT_REPO_PATH` untuk menentukan lokasi repositori sementara.

*   **`requirements.txt` (Modifikasi):**
    *   Menambahkan `pytest` untuk pengujian.

*   **`services/gitlab_service.py` (Modifikasi):**
    *   Memperbaiki regex untuk `_parse_project_path_from_mr_url` dan `_parse_project_path_from_commit_url` untuk parsing project path yang lebih akurat.

## 4. Pengujian Komprehensif

Pengujian komprehensif dilakukan menggunakan `pytest` untuk memverifikasi fungsionalitas, performa, dan stabilitas solusi baru. File `tests/test_diff_fetching.py` dibuat untuk tujuan ini.

### Test Case Utama:

1.  **`test_fetch_commit_diff_local_success`**: Memverifikasi bahwa `DiffFetcher` berhasil mengambil diff commit menggunakan `GitService` lokal ketika semua kondisi terpenuhi.
2.  **`test_fetch_commit_diff_fallback_to_gitlab_api_clone_fails`**: Memverifikasi bahwa `DiffFetcher` beralih ke GitLab API jika `GitService` gagal mengkloning repositori.
3.  **`test_fetch_commit_diff_fallback_to_gitlab_api_get_diff_fails`**: Memverifikasi bahwa `DiffFetcher` beralih ke GitLab API jika `GitService` berhasil mengkloning tetapi gagal mengambil diff lokal.
4.  **`test_fetch_gitlab_mr_diff`**: Memverifikasi bahwa pengambilan diff MR secara konsisten menggunakan `GitLabService`.
5.  **`test_get_repo_name_from_url_mr_url`**, **`test_get_repo_name_from_url_commit_url`**, **`test_get_repo_name_from_url_direct_repo_url`**: Memverifikasi fungsionalitas penguraian URL di `GitService`.
6.  **`test_clone_repository_new_clone`**: Memverifikasi kloning repositori baru oleh `GitService`.
7.  **`test_clone_repository_existing_pull`**: Memverifikasi perilaku `git pull` untuk repositori yang sudah ada.
8.  **`test_get_commit_diff_success`**: Memverifikasi pengambilan diff commit yang berhasil dari repositori lokal oleh `GitService`.

### Hasil Pengujian:

Semua 11 test case berhasil dilalui. Ini mengonfirmasi bahwa:

*   Logika fallback di `DiffFetcher` berfungsi dengan benar.
*   `GitService` dapat mengkloning repositori, melakukan pull, dan mengambil diff commit dari repositori lokal.
*   Parsing URL di `GitService` dan `GitLabService` (yang dimodifikasi) berfungsi sebagaimana mestinya.
*   Fungsionalitas pengambilan diff MR melalui GitLab API tidak terpengaruh.

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: d:\Programmer\Project\Python\sa_automation
plugins: anyio-4.12.1
collected 11 items

tests\test_diff_fetching.py ...........                                  [100%]

============================== warnings summary ===============================
C:\Users\vananda.rahadika\AppData\Local\Programs\Python\Python314\Lib\site-packages\google\genai\types.py:43
  C:\Users\vananda.rahadika\AppData\Local\Programs\Python\Python314\Lib\site-packages\google\genai\types.py:43: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 11 passed, 1 warning in 14.69s ========================
```

_Catatan: Peringatan `DeprecationWarning` dari `google.genai.types.py` adalah masalah pihak ketiga dan tidak memengaruhi fungsionalitas solusi yang diterapkan._

## 5. Analisis Perbandingan Terhadap Metode Sebelumnya

| Fitur / Metrik | Metode Sebelumnya (GitLab API Only) | Metode Baru (Lokal Git + GitLab API Fallback) |
| :------------------- | :------------------------------------------------------------------ | :---------------------------------------------------------------------- |
| **Keandalan** | Rentan terhadap masalah API GitLab (rate limit, downtime, kesalahan). | Sangat meningkat dengan mekanisme fallback lokal. Lebih tahan terhadap masalah API. |
| **Performa** | Sepenuhnya bergantung pada latensi jaringan dan respons API GitLab. | Berpotensi lebih cepat untuk pengambilan diff commit setelah kloning awal, karena operasi lokal lebih cepat. |
| **Efisiensi** | Setiap permintaan diff commit atau MR membebani API GitLab. | Mengurangi beban API GitLab untuk diff commit, menggunakan sumber daya lokal. |
| **Akurasi** | Akurat selama API merespons dengan benar. | Akurat, karena mengambil diff langsung dari repositori (lokal atau API). |
| **Fleksibilitas** | Terbatas pada apa yang ditawarkan oleh API GitLab. | Lebih fleksibel, dapat disesuaikan untuk berbagai skenario pengambilan diff Git lokal. |
| **Kompleksitas Kode**| Cukup sederhana, satu titik integrasi. | Sedikit lebih kompleks karena memerlukan manajemen repositori lokal dan logika fallback. |
| **Dependencies** | `python-gitlab` | `python-gitlab`, `git` CLI (harus terinstal pada sistem) |

**Kesimpulan Perbandingan:**

Solusi baru ini secara signifikan meningkatkan keandalan dan efisiensi mekanisme pengambilan diff, terutama untuk commit. Dengan memperkenalkan `GitService` lokal, sistem tidak lagi sepenuhnya bergantung pada ketersediaan dan kinerja GitLab API, menyediakan jalur yang lebih kuat untuk mendapatkan data diff. Meskipun ada sedikit peningkatan kompleksitas kode, manfaat dalam keandalan dan potensi peningkatan kinerja membenarkan perubahan ini.

## 6. Kesimpulan

Mekanisme pengambilan perbedaan yang diperbarui, dengan prioritas operasi Git lokal dan fallback ke GitLab API, merupakan solusi yang tangguh dan efisien. Pengujian komprehensif mengonfirmasi fungsionalitas dan stabilitasnya. Implementasi ini akan secara signifikan meningkatkan keandalan dan kinerja fitur tinjauan kode otomatis.

## 7. Cara Menjalankan

Untuk menjalankan aplikasi dengan mekanisme pengambilan diff yang baru, ikuti langkah-langkah berikut:

1.  **Pastikan Dependensi Terinstal**:
    Pastikan semua dependensi yang diperlukan terinstal. Jika Anda baru saja memodifikasi `requirements.txt`, jalankan perintah ini:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Konfigurasi Variabel Lingkungan**:
    Pastikan file `.env` Anda berisi variabel lingkungan yang diperlukan, termasuk `LOCAL_GIT_REPO_PATH` jika Anda ingin menyesuaikan direktori repositori lokal. Contoh `.env`:
    ```
    JIRA_SERVER=your_jira_server_url
    JIRA_PAT=your_jira_personal_access_token
    GITLAB_SERVER=your_gitlab_server_url
    GITLAB_PRIVATE_TOKEN=your_gitlab_private_token
    AI_SERVICE_PROVIDER=gemini # atau openai
    GEMINI_API_KEY=your_gemini_api_key
    OPENAI_API_KEY=your_openai_api_key
    LOCAL_GIT_REPO_PATH=temp_repos # Direktori untuk kloning repositori lokal (opsional, default: temp_repos)
    ```

3.  **Jalankan Aplikasi**:
    Anda memiliki dua opsi untuk menjalankan analisis:

    *   **Analisis Tiket Jira (seperti sebelumnya)**:
        Gunakan perintah `python main.py` dengan argumen `--ticket` untuk memulai analisis pada tiket Jira tertentu. Aplikasi akan secara otomatis mencoba mengambil diff untuk URL commit atau merge request yang ditemukan dalam deskripsi atau komentar tiket Jira. `DiffFetcher` akan memprioritaskan pengambilan diff commit secara lokal melalui `GitService` (dengan mengkloning repositori ke `LOCAL_GIT_REPO_PATH`) dan akan kembali ke GitLab API jika pengambilan lokal gagal. Untuk merge request, aplikasi akan selalu menggunakan GitLab API.
        
        Contoh:
        ```bash
        python main.py --ticket PCC-2035 --ai-provider openai
        ```

    *   **Analisis Repositori Lokal**:
        Jika Anda memiliki proyek secara lokal dan ingin menganalisis commit tertentu tanpa melalui Jira, Anda dapat menggunakan argumen `--local-repo-path` dan `--commit-sha`. Ini akan memungkinkan Anda untuk langsung menganalisis diff dari repositori lokal Anda.
        
        Contoh:
        ```bash
        python main.py --local-repo-path "C:/path/to/your/local/repo" --commit-sha "your_commit_sha_here" --ai-provider openai
        ```
        
        Dalam mode ini, aplikasi akan:
        *   Langsung menggunakan `GitService` untuk mengambil diff commit dari jalur repositori lokal yang Anda berikan.
        *   Melewatkan langkah-langkah pencarian URL GitLab di Jira.
        *   Menganalisis diff dengan AI dan mencetak hasilnya langsung ke konsol. Tidak ada komentar Jira yang akan diposting dalam mode ini.
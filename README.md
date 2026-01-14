# 🤖 Automated Code Reviewer

Aplikasi CLI untuk mengotomatisasi code review menggunakan AI (Gemini/OpenAI). Mengekstrak link Merge Request atau Commit dari tiket Jira, menganalisis perubahan kode, dan mem-posting hasil review ke Jira.

## ⚡ Quick Start

```bash
# 1. Clone & masuk direktori
git clone https://github.com/your-repo/automated-code-reviewer.git
cd automated-code-reviewer

# 2. Setup virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup konfigurasi
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux

# 5. Edit file .env dengan kredensial Anda (lihat bagian Konfigurasi di bawah)

# 6. Jalankan!
# Jalankan untuk satu tiket
python main.py --ticket "PROJ-123"

# Jalankan untuk beberapa tiket sekaligus (pisahkan dengan koma)
python main.py --ticket "PROJ-123,PROJ-456" --ai-provider openai
```

## 📋 Konfigurasi (.env)

Buat file `.env` berdasarkan `.env.example` dan isi:

```env
# Jira
JIRA_SERVER="https://your-jira.atlassian.net"
JIRA_PAT="your_jira_personal_access_token"

# GitLab
GITLAB_SERVER="https://gitlab.com"
GITLAB_PRIVATE_TOKEN="your_gitlab_token"

# AI Provider (pilih salah satu: gemini atau openai)
AI_SERVICE_PROVIDER="gemini"

# Untuk Gemini
GEMINI_API_KEY="your_gemini_api_key"

# Untuk OpenAI/OpenRouter
OPENAI_API_KEY="your_openai_key"
OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# --- Workflow Configuration ---
# Set "true" untuk otomatis klik tombol "Revisi" jika AI merekomendasikan.
# Tidak mempengaruhi transisi "Staging".
AUTO_TRANSITION_REVISI="true"
```

### Cara Mendapatkan API Keys:
| Service | Cara Mendapatkan |
|---------|------------------|
| **Gemini** | [Google AI Studio](https://aistudio.google.com/apikey) - Gratis |
| **Jira PAT** | Profile → Personal Access Tokens → Create token |
| **GitLab Token** | Settings → Access Tokens → Create dengan scope `api` |

## 🚀 Cara Penggunaan

### Review Satu Tiket Jira
```bash
# Menggunakan provider AI default dari .env
python main.py --ticket "PCC-1234"

# Menggunakan provider AI spesifik (override .env)
python main.py --ticket "PCC-1234" --ai-provider openai
```

### Review Beberapa Tiket Jira Sekaligus
Pisahkan ID tiket dengan koma.
```bash
python main.py --ticket "PCC-1234,PCC-5678,PCC-9012"
```

### Review Local Repository
```bash
python main.py --local-repo-path "C:\path\to\repo" --commit-sha "abc123" --ai-provider gemini
```

## ✨ Fitur

- 🔍 **Auto-detect bahasa** - Java, JavaScript, Python, dll
- 🇮🇩 **Output Bahasa Indonesia** - Hasil review dalam Bahasa Indonesia
- 📝 **Komentar actionable** - Langsung dengan kode perbaikan copy-paste
- 🔗 **Smart URL detection** - Mengambil link commit/MR terakhir dari komentar Jira
- ⚡ **Multi AI provider** - Support Gemini dan OpenAI/OpenRouter

## 📁 Struktur Proyek

```
automated-code-reviewer/
├── main.py              # Entry point aplikasi
├── config/
│   └── settings.py      # Konfigurasi environment
├── services/
│   ├── ai_service.py    # Koneksi ke AI (Gemini/OpenAI)
│   ├── jira_service.py  # Koneksi ke Jira
│   ├── gitlab_service.py# Koneksi ke GitLab
│   └── git_service.py   # Git operations
├── prompts/
│   └── code_review_prompt.txt  # Template prompt AI
├── requirements.txt     # Python dependencies
└── .env.example         # Template konfigurasi
```

## 🛠️ Requirements

- Python 3.10+
- Akses ke Jira dan GitLab
- API Key Gemini atau OpenAI

## 📄 License

MIT License
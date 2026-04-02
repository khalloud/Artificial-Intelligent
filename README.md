# X-Bookmarks Intelligence Engine 🧠

Transform your scattered X (Twitter) bookmarks into a structured, searchable, and AI-curated knowledge base.

## 🚀 Overview

This tool processes raw X bookmark export data and uses Gemini AI to:
- **Categorize**: Automatically group tweets into relevant topics (e.g., AI Engineering, Venture Capital, Crypto).
- **Summarize**: Generate concise 1-sentence insights for every bookmark.
- **Rank**: Assign importance scores (1-5 stars) to help you surface the best content.
- **Visualize**: Generate a premium, dark-mode Searchable Dashboard (HTML) with zero external dependencies.

## 🛠️ Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd x-bookmarks-intel
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Key**:
   Create a `.env` file in the root directory and add your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

## 📖 Usage

1. **Export your bookmarks**: Use a tool (like the "X Bookmark Extractor" Chrome Extension) to get your bookmarks as a `json` file.
2. **Run the Engine**:
   ```bash
   python3 intel_engine.py --input bookmarks.json --output my_knowledge_base.html
   ```
3. **View the results**: Open the generated `my_knowledge_base.html` in any modern web browser.

## 🛡️ Privacy & Technicals

- **Model**: Powered by `gemini-2.0-flash` for high-speed analysis.
- **Caching**: All AI analysis is saved to `enriched_data.json` so you never pay for the same item twice and can resume interrupted runs.
- **Dashboard**: Built with Tailwind CSS and Alpine.js (loaded via CDN).

---
*Built with love for organized thinkers.*

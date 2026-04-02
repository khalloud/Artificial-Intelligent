import os
import json
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from tqdm import tqdm
from jinja2 import Template

# Setup
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# Use Flash for speed with thousands of items
MODEL_NAME = "gemini-2.0-flash"

SYSTEM_PROMPT = """
You are a highly intelligent knowledge curator. Your task is to analyze a batch of X (Twitter) bookmarks and help organize them into a searchable digital garden.

For each bookmark provided in the JSON, you must:
1.  **Assign a Topic**: Create a concise topic/category name (e.g., 'AI Engineering', 'Life Hacks', 'Market Research', 'Philosophy'). Be specific but consistent across items in this batch.
2.  **Generate a TL;DR**: A one-sentence summary that captures the core value of the content.
3.  **Rank Importance**: On a scale of 1 to 5 (5 is highly valuable content, 1 is noise or short banter).

Response Format:
Return ONLY a valid JSON object where keys are the 'id' of the bookmark and values are objects like:
{
  "tweetId123": {"topic": "Topic Name", "summary": "One sentence summary.", "rank": 5},
  ...
}
Do NOT include any extra text or markdown formatting in your response. Just the JSON.
"""

def classify_batch(batch_items):
    # Format input for AI
    input_data = []
    for item in batch_items:
        input_data.append({
            "id": item.get('id'),
            "author": item.get('authorName'),
            "text": item.get('text')
        })
    
    prompt = f"Batch to analyze:\n{json.dumps(input_data)}\n\nFollow the system instructions to classify these bookmarks."
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={'system_instruction': SYSTEM_PROMPT}
        )
        # Strip potential markdown formatting from AI response
        cleaned_json = response.text.strip().lstrip("```json").rstrip("```").strip()
        return json.loads(cleaned_json)
    except Exception as e:
        print(f"\nError processing batch: {e}")
        time.sleep(2) # Basic backoff
        return {}

def process_bookmarks(input_file, output_file, batch_size=20):
    with open(input_file, "r") as f:
        all_bookmarks = json.load(f)
    
    # Load existing progress if any
    enriched_data = {}
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            enriched_data = json.load(f)
    
    # Filter out already processed
    to_process = [b for b in all_bookmarks if b.get('id') not in enriched_data]
    
    if not to_process:
        print("All bookmarks already processed!")
        return all_bookmarks, enriched_data

    print(f"Total: {len(all_bookmarks)} | New: {len(to_process)}")
    
    # Process in batches
    for i in tqdm(range(0, len(to_process), batch_size), desc="AI Classification"):
        batch = to_process[i:i+batch_size]
        results = classify_batch(batch)
        
        # Merge results
        for tid, metadata in results.items():
            enriched_data[tid] = metadata
            
        # Intermediate save (every batch)
        with open(output_file, "w") as f:
            json.dump(enriched_data, f, indent=2)
            
    return all_bookmarks, enriched_data

# PREMIUM HTML TEMPLATE (Enhanced for large datasets)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Knowledge Base Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <style>
        body { font-family: 'Outfit', sans-serif; background-color: #0f172a; color: #f8fafc; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .card:hover { transform: translateY(-4px); transition: all 0.3s ease; }
        [x-cloak] { display: none !important; }
    </style>
</head>
<body x-data="{ 
    search: '', 
    selectedTopic: 'All',
    bookmarks: [],
    loading: true,
    init() {
        try {
            const data = document.getElementById('bookmarks-data').textContent;
            this.bookmarks = JSON.parse(data);
            this.loading = false;
        } catch (e) {
            console.error('Failed to parse bookmarks data', e);
        }
    },
    get filteredBookmarks() {
        if (!this.bookmarks) return [];
        return this.bookmarks.filter(b => {
             const matchSearch = b.text.toLowerCase().includes(this.search.toLowerCase()) || 
                                b.authorName.toLowerCase().includes(this.search.toLowerCase()) ||
                                (b.topic && b.topic.toLowerCase().includes(this.search.toLowerCase()));
             const matchTopic = this.selectedTopic === 'All' || b.topic === this.selectedTopic;
             return matchSearch && matchTopic;
        });
    },
    get topics() {
        if (!this.bookmarks) return ['All'];
        const t = new Set(this.bookmarks.map(b => b.topic).filter(Boolean));
        return ['All', ...Array.from(t).sort()];
    }
}" x-cloak>
    <div class="min-h-screen p-6 md:p-12">
        <header class="max-w-7xl mx-auto mb-12">
            <h1 class="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-4">
                My X Knowledge Base
            </h1>
            <p class="text-slate-400 text-lg">Thousands of insights, curated by AI.</p>
        </header>

        <section class="max-w-7xl mx-auto space-y-8">
            <!-- Controls -->
            <div class="glass p-6 rounded-2xl flex flex-col md:flex-row gap-4 items-center justify-between">
                <div class="relative w-full md:w-1/2">
                    <input type="text" x-model="search" placeholder="Search keywords, authors, topics..." 
                           class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none transition-all">
                </div>
                <div class="flex gap-2 flex-wrap justify-center">
                    <template x-for="topic in topics" :key="topic">
                        <button @click="selectedTopic = topic"
                                :class="selectedTopic === topic ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'"
                                class="px-4 py-2 rounded-full text-sm font-semibold transition-all"
                                x-text="topic"></button>
                    </template>
                </div>
            </div>

            <!-- Stats -->
            <div class="text-slate-500 text-sm">
                Showing <span class="text-blue-400 font-bold" x-text="filteredBookmarks.length"></span> bookmarks
            </div>

            <!-- Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <template x-for="bookmark in filteredBookmarks" :key="bookmark.id">
                    <div class="card glass p-6 rounded-2xl flex flex-col justify-between">
                        <div>
                            <div class="flex justify-between items-start mb-4">
                                <span class="bg-blue-900/40 text-blue-300 text-xs font-bold px-2 py-1 rounded uppercase tracking-wider" x-text="bookmark.topic || 'Uncategorized'"></span>
                                <div class="flex gap-1 text-yellow-500">
                                    <template x-for="i in (bookmark.rank || 0)">
                                        <span>★</span>
                                    </template>
                                </div>
                            </div>
                            <p class="text-slate-100 text-sm font-semibold mb-3 italic" x-text="bookmark.summary"></p>
                            <p class="text-slate-400 text-sm line-clamp-4 mb-4" x-text="bookmark.text"></p>
                        </div>
                        <div class="pt-4 border-t border-slate-700/50 flex justify-between items-center text-xs">
                            <div class="flex flex-col">
                                <span class="text-slate-300 font-bold" x-text="bookmark.authorName"></span>
                                <span class="text-slate-500" x-text="'@'+bookmark.authorHandle"></span>
                            </div>
                            <a :href="bookmark.url" target="_blank" class="text-blue-400 hover:text-blue-300 font-bold flex items-center gap-1">
                                View Tweet
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                            </a>
                        </div>
                    </div>
                </template>
            </div>
        </section>
    </div>
    <!-- Data Script Tag -->
    <script id="bookmarks-data" type="application/json">{{ bookmarks_json }}</script>
</body>
</html>
"""

def generate_html(all_bookmarks, enriched_data, output_file):
    # Merge datasets
    final_list = []
    for b in all_bookmarks:
        meta = enriched_data.get(b.get('id'), {})
        final_list.append({
            **b,
            "topic": meta.get('topic', 'General'),
            "summary": meta.get('summary', ''),
            "rank": meta.get('rank', 1)
        })
    
    # Sort by rank descending
    final_list.sort(key=lambda x: (x.get('rank', 0), x.get('timestamp', '')), reverse=True)
    
    # Render template
    template = Template(HTML_TEMPLATE)
    html_content = template.render(bookmarks_json=json.dumps(final_list))
    
    with open(output_file, "w") as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description="X-Bookmarks Intelligence Engine")
    parser.add_argument("--input", required=True, help="Path to raw JSON bookmarks file")
    parser.add_argument("--output", default="knowledge_base.html", help="Path to final HTML output")
    parser.add_argument("--batch", type=int, default=25, help="Tokens/Batch size")
    args = parser.parse_args()

    input_path = Path(args.input)
    enrich_path = input_path.parent / "enriched_data.json"
    
    print(f"--- X-Intelligence Engine Started ---")
    
    all_bookmarks, enriched_data = process_bookmarks(args.input, enrich_path, batch_size=args.batch)
    
    print(f"\nGenerating Searchable Knowledge Base...")
    generate_html(all_bookmarks, enriched_data, args.output)
    
    print(f"Success! Your knowledge base is ready: {args.output}")

if __name__ == "__main__":
    main()

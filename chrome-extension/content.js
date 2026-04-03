let scrapingInterval = null;
let lastScrollHeight = 0;
let sameHeightRetries = 0;
const MAX_RETRIES = 5;

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'START_SCRAPING') {
    startScraping();
    sendResponse({ status: 'started' });
  } else if (request.action === 'STOP_SCRAPING') {
    stopScraping(false);
  }
});

function startScraping() {
  if (scrapingInterval) return;
  lastScrollHeight = 0;
  sameHeightRetries = 0;

  console.log('X Bookmark Exporter: Started scraping...');
  
  // Set an interval to parse the DOM and scroll down
  scrapingInterval = setInterval(async () => {
    // 1. Scrape currently visible tweets
    await extractAndSaveBookmarks();
    
    // 2. Scroll down
    window.scrollBy(0, window.innerHeight * 1.5);
    
    // 3. Check if reached bottom
    const currentScrollHeight = document.documentElement.scrollHeight;
    if (currentScrollHeight === lastScrollHeight) {
      sameHeightRetries++;
      if (sameHeightRetries >= MAX_RETRIES) {
        console.log('X Bookmark Exporter: Reached bottom of the page.');
        stopScraping(true);
      }
    } else {
      sameHeightRetries = 0;
      lastScrollHeight = currentScrollHeight;
    }
  }, 1500); // 1.5s delay to allow React to render new tweets
}

function stopScraping(completed) {
  if (scrapingInterval) {
    clearInterval(scrapingInterval);
    scrapingInterval = null;
    console.log('X Bookmark Exporter: Stopped scraping.');
  }
  if (completed) {
    chrome.runtime.sendMessage({ action: 'SCRAPE_COMPLETE' });
  }
}

async function extractAndSaveBookmarks() {
  const articles = document.querySelectorAll('article[data-testid="tweet"]');
  const newBookmarks = [];

  articles.forEach(article => {
    try {
      // 1. Extract URL & ID (from the time element's anchor)
      const timeAnchor = article.querySelector('time')?.closest('a');
      const url = timeAnchor ? timeAnchor.href : null;
      if (!url) return; // Not a standard tweet or AD

      const urlObj = new URL(url);
      const tweetId = urlObj.pathname.split('/').pop();

      // 2. Extract Author Details
      const userNamesContainer = article.querySelector('[data-testid="User-Name"]');
      let authorName = null;
      let authorHandle = null;

      if (userNamesContainer) {
        const spans = userNamesContainer.querySelectorAll('span');
        if (spans.length > 0) authorName = spans[0].innerText;
        
        const anchors = userNamesContainer.querySelectorAll('a[href^="/"]');
        Array.from(anchors).forEach(a => {
          if (a.innerText.startsWith('@')) {
            authorHandle = a.innerText;
          }
        });
      }

      // 3. Extract Text
      const textContainer = article.querySelector('div[data-testid="tweetText"]');
      const text = textContainer ? textContainer.innerText : '';

      // 4. Extract Timestamp
      const timeEl = article.querySelector('time');
      const timestamp = timeEl ? timeEl.getAttribute('datetime') : null;

      newBookmarks.push({
        id: tweetId,
        url: url,
        authorName: authorName,
        authorHandle: authorHandle,
        text: text,
        timestamp: timestamp,
        scrapedAt: new Date().toISOString()
      });
    } catch (e) {
      console.error('Error parsing tweet:', e);
    }
  });

  if (newBookmarks.length > 0) {
    await saveToStorage(newBookmarks);
  }
}

function saveToStorage(newBookmarks) {
  return new Promise(resolve => {
    chrome.storage.local.get(['bookmarks'], (result) => {
      const existingBookmarks = result.bookmarks || [];
      const bookmarkMap = new Map();

      // Populate map with existing to ensure uniqueness by ID
      existingBookmarks.forEach(b => {
        if (b.id) bookmarkMap.set(b.id, b);
      });

      // Add new ones
      newBookmarks.forEach(b => {
        if (b.id) bookmarkMap.set(b.id, b);
      });

      const updatedBookmarks = Array.from(bookmarkMap.values());
      
      // Sort by timestamp descending
      updatedBookmarks.sort((a, b) => {
        if (!a.timestamp) return 1;
        if (!b.timestamp) return -1;
        return new Date(b.timestamp) - new Date(a.timestamp);
      });

      chrome.storage.local.set({ bookmarks: updatedBookmarks }, () => {
        resolve();
      });
    });
  });
}

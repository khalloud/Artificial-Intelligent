document.addEventListener('DOMContentLoaded', () => {
  const countEl = document.getElementById('count');
  const startBtn = document.getElementById('start-btn');
  const stopBtn = document.getElementById('stop-btn');
  const exportBtn = document.getElementById('export-btn');
  const clearBtn = document.getElementById('clear-btn');
  const statusEl = document.getElementById('status');
  const scrapeLoader = document.getElementById('scrape-loader');
  const startBtnText = startBtn.querySelector('.btn-text');

  // Load current count
  const updateCount = () => {
    chrome.storage.local.get(['bookmarks'], (result) => {
      const bookmarks = result.bookmarks || [];
      countEl.textContent = bookmarks.length;
    });
  };

  updateCount();
  
  // Listen for storage changes to update count live
  chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'local' && changes.bookmarks) {
      countEl.textContent = changes.bookmarks.newValue.length;
    }
  });

  const setStatus = (msg, isSuccess = false) => {
    statusEl.textContent = msg;
    if (isSuccess) {
      statusEl.classList.add('success-text');
    } else {
      statusEl.classList.remove('success-text');
    }
    setTimeout(() => { statusEl.textContent = ''; }, 4000);
  };

  startBtn.addEventListener('click', async () => {
    let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url.includes('x.com/i/bookmarks') && !tab.url.includes('twitter.com/i/bookmarks')) {
      setStatus('Please open your X bookmarks page first.');
      return;
    }

    // Toggle UI
    startBtnText.textContent = 'Scraping...';
    scrapeLoader.classList.remove('hidden');
    startBtn.disabled = true;
    stopBtn.classList.remove('hidden');

    chrome.tabs.sendMessage(tab.id, { action: 'START_SCRAPING' }, (response) => {
      if (chrome.runtime.lastError) {
        setStatus('Error: Refresh the bookmarks page and try again.');
        resetScrapeUI();
      } else {
        setStatus('Scraping started...', true);
      }
    });
  });

  stopBtn.addEventListener('click', async () => {
    let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.tabs.sendMessage(tab.id, { action: 'STOP_SCRAPING' });
    resetScrapeUI();
    setStatus('Scraping stopped.', true);
  });

  // Also listen for completion message from content script
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'SCRAPE_COMPLETE') {
      resetScrapeUI();
      setStatus('Scraping complete! Reached the end.', true);
    }
  });

  function resetScrapeUI() {
    startBtnText.textContent = 'Start Auto-Scraping';
    scrapeLoader.classList.add('hidden');
    startBtn.disabled = false;
    stopBtn.classList.add('hidden');
  }

  exportBtn.addEventListener('click', () => {
    chrome.storage.local.get(['bookmarks'], (result) => {
      const bookmarks = result.bookmarks || [];
      if (bookmarks.length === 0) {
        setStatus('No bookmarks to export.');
        return;
      }

      const jsonStr = JSON.stringify(bookmarks, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `x-bookmarks-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      
      URL.revokeObjectURL(url);
      setStatus('Export successful!', true);
    });
  });

  clearBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear all saved bookmarks data from local storage?')) {
      chrome.storage.local.set({ bookmarks: [] }, () => {
        updateCount();
        setStatus('Data cleared.', true);
      });
    }
  });
});

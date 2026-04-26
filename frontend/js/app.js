/**
 * FotoDerp - Frontend Application
 * 
 * Communicates with the Python backend via Electron IPC.
 */

document.addEventListener('DOMContentLoaded', () => {
  console.log('[FotoDerp] App started');
  
  // State
  const state = {
    currentPage: 1,
    perPage: 50,
    totalPhotos: 0,
    selectedPhoto: null,
    currentView: 'all',
    searchQuery: '',
    selectedTags: [],
  };

  // --- Star Rating Component ---
  function createStarRating(rating = 0, onChange) {
    const container = document.createElement('div');
    container.className = 'star-rating';
    container.style.display = 'flex';
    container.style.gap = '4px';

    for (let i = 1; i <= 5; i++) {
      const star = document.createElement('span');
      star.textContent = i <= rating ? '★' : '☆';
      star.style.cursor = 'pointer';
      star.style.fontSize = '18px';
      star.style.color = i <= rating ? 'var(--accent)' : 'var(--text-secondary)';
      star.addEventListener('click', () => onChange(i));
      star.addEventListener('mouseenter', () => {
        container.querySelectorAll('span').forEach((s, idx) => {
          s.textContent = idx < i ? '★' : '☆';
          s.style.color = idx < i ? 'var(--accent)' : 'var(--text-secondary)';
        });
      });
      star.addEventListener('mouseleave', () => {
        container.querySelectorAll('span').forEach((s, idx) => {
          s.textContent = idx < rating ? '★' : '☆';
          s.style.color = idx < rating ? 'var(--accent)' : 'var(--text-secondary)';
        });
      });
      container.appendChild(star);
    }
    return container;
  }

  // DOM Elements
  const elements = {
    searchInput: document.getElementById('search-input'),
    photoGrid: document.getElementById('photo-grid'),
    prevPage: document.getElementById('prev-page'),
    nextPage: document.getElementById('next-page'),
    pageInfo: document.getElementById('page-info'),
    statusLeft: document.getElementById('status-left'),
    statusRight: document.getElementById('status-right'),
    previewPanel: document.getElementById('preview-panel'),
    btnImport: document.getElementById('btn-import'),
    btnAnalyze: document.getElementById('btn-analyze'),
    viewToggle: document.getElementById('view-toggle'),
    tagsList: document.getElementById('tags-list'),
    personsList: document.getElementById('persons-list'),
  };

  // --- Backend Communication ---

  async function callBackend(method, endpoint, data = null) {
    try {
      const result = await window.fotoerp.backendRequest(method, endpoint, data);
      return result;
    } catch (error) {
      console.error('[FotoDerp] Backend error:', error);
      updateStatus('Backend unreachable', 'error');
      return null;
    }
  }

  // --- Photo Loading ---

  async function loadPhotos() {
    updateStatus('Loading images...');
    
    const params = new URLSearchParams({
      page: state.currentPage,
      per_page: state.perPage,
    });

    // Use search endpoint for text queries
    if (state.searchQuery) {
      params.set('query', state.searchQuery);
    }

    const result = await callBackend('GET', `/api/search?${params}`);
    
    if (result) {
      const photos = result.results || [];
      renderPhotos(photos);
      state.totalPhotos = result.total || photos.length;
      updatePagination();
    } else {
      // Fallback: try direct photo listing without search
      const fallbackResult = await callBackend('GET', `/api/photos?${params}`);
      if (fallbackResult) {
        renderPhotos(fallbackResult.photos || []);
        state.totalPhotos = fallbackResult.total || 0;
        updatePagination();
      }
    }
    
    updateStatus(`${state.totalPhotos} images loaded`);
  }

  async function renderPhotos(photos) {
    elements.photoGrid.innerHTML = '';
    
    if (photos.length === 0) {
      elements.photoGrid.innerHTML = `
        <div class="photo-placeholder">
          <div class="placeholder-icon">📷</div>
          <span>No images imported yet</span>
        </div>
      `;
      return;
    }

    for (const photo of photos) {
      const item = document.createElement('div');
      item.className = 'photo-item';
      item.dataset.photoId = photo.id;
      
      // Try to get image via IPC (handles local files, RAW, etc.)
      const img = document.createElement('img');
      img.alt = photo.filename;
      img.loading = 'lazy';
      
      // Load image via Electron IPC (works for any file type)
      if (photo.path && window.fotoerp.imageBlobUrl) {
        const blobUrl = await window.fotoerp.imageBlobUrl(photo.path);
        if (blobUrl) {
          img.src = blobUrl;
        } else {
          // Fallback: show placeholder
          img.src = '';
          img.alt = '⚠️';
          img.style.fontSize = '32px';
          img.style.display = 'flex';
          img.style.alignItems = 'center';
          img.style.justifyContent = 'center';
        }
      } else {
        // Browser dev mode: try relative path
        img.src = `/api/photos/${photo.id}/preview`;
      }
      
      // Overlay with filename
      const overlay = document.createElement('div');
      overlay.className = 'photo-overlay';
      overlay.textContent = photo.filename;
      
      item.appendChild(img);
      item.appendChild(overlay);
      item.addEventListener('click', () => selectPhoto(photo));
      
      elements.photoGrid.appendChild(item);
    }
  }

  // --- Photo Selection & Preview ---

  async function selectPhoto(photo) {
    state.selectedPhoto = photo;
    updateStatus(`Selected: ${photo.filename}`);
    
    // Load detail view
    const result = await callBackend('GET', `/api/photos/${photo.id}`);
    
    if (result) {
      renderPreview(result);
    }
  }

  async function renderPreview(photo) {
    // Load image via IPC for local file access
    let imageUrl = '';
    if (photo.path && window.fotoerp.imageBlobUrl) {
      imageUrl = await window.fotoerp.imageBlobUrl(photo.path) || '';
    }

    // Build analyses display
    const analysesList = (photo.analyses || []).map(a => {
      const data = typeof a.data === 'string' ? JSON.parse(a.data) : a.data;
      return `<div class="analysis-item">
        <strong>${a.type}</strong>: ${JSON.stringify(data)}
      </div>`;
    }).join('');

    // Build tags display
    const tagsList = (photo.tags || []).map(tag =>
      `<span class="preview-tag" data-tag-id="${tag.id}">${tag.name}</span>`
    ).join('');

    const rating = photo.rating || 0;

    elements.previewPanel.innerHTML = `
      <div class="preview-image-container">
        ${imageUrl ?
          `<img src="${imageUrl}" alt="${photo.filename}" class="preview-image">` :
          `<div class="preview-placeholder">Image not available</div>`
        }
      </div>
      <div class="preview-meta">
        <h4>${photo.filename}</h4>
        <p>Size: ${photo.width || '?'}×${photo.height || '?'}</p>
        <p>Format: ${photo.format || 'unknown'}</p>
        <p>Captured: ${photo.captured_at || 'Unknown'}</p>
        ${photo.gps_lat ? `<p>Location: ${photo.gps_lat}, ${photo.gps_lon}</p>` : ''}
        <p>Status: ${photo.status || 'unknown'}</p>

        <h4 style="margin-top: 12px;">Rating</h4>
        <div id="star-rating-container"></div>

        <h4 style="margin-top: 12px;">Tags</h4>
        <div class="preview-tags">
          ${tagsList || '<span style="color: var(--text-secondary)">No tags</span>'}
        </div>

        ${analysesList ? `
          <h4 style="margin-top: 12px;">KI Analyses</h4>
          <div class="preview-analyses">
            ${analysesList}
          </div>
        ` : ''}
      </div>
    `;

    // Render star rating component
    const ratingContainer = elements.previewPanel.querySelector('#star-rating-container');
    if (ratingContainer) {
      createStarRating(rating, async (newRating) => {
        await callBackend('PUT', `/api/photos/${photo.id}/rating`, { rating: newRating });
        // Reload photo to get updated rating
        const result = await callBackend('GET', `/api/photos/${photo.id}`);
        if (result) renderPreview(result);
      });
    }
  }

  // --- Favorites Loading ---

  async function loadFavorites() {
    updateStatus('Loading favorites...');

    const params = new URLSearchParams({
      page: state.currentPage,
      per_page: state.perPage,
    });

    const result = await callBackend('GET', `/api/photos/favorites?${params}`);

    if (result) {
      renderPhotos(result.photos || []);
      state.totalPhotos = result.total || 0;
      updatePagination();
    }

    updateStatus(`${state.totalPhotos} favorites loaded`);
  }

  // --- Search ---

  let searchTimeout;
  elements.searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
      state.searchQuery = e.target.value.trim();
      state.currentPage = 1;
      await loadPhotos();
    }, 300);
  });

  // --- Pagination ---

  elements.prevPage.addEventListener('click', async () => {
    if (state.currentPage > 1) {
      state.currentPage--;
      await loadPhotos();
    }
  });

  elements.nextPage.addEventListener('click', async () => {
    const maxPage = Math.ceil(state.totalPhotos / state.perPage);
    if (state.currentPage < maxPage) {
      state.currentPage++;
      await loadPhotos();
    }
  });

  function updatePagination() {
    const maxPage = Math.ceil(state.totalPhotos / state.perPage);
    elements.pageInfo.textContent = `Page ${state.currentPage} of ${maxPage || 1}`;
    elements.prevPage.disabled = state.currentPage <= 1;
    elements.nextPage.disabled = state.currentPage >= maxPage;
  }

  // --- Import ---

  elements.btnImport.addEventListener('click', async () => {
    const folders = await window.fotoerp.selectFolder();
    if (folders && folders.length > 0) {
      updateStatus(`Importing: ${folders.join(', ')}`);
      
      const result = await callBackend('POST', '/api/photos/import', {
        paths: folders,
      });
      
      if (result) {
        updateStatus(`${result.imported} images imported`);
        loadPhotos();
      }
    }
  });

  // --- Analysis ---

  elements.btnAnalyze.addEventListener('click', async () => {
    updateStatus('Starting KI analysis...');
    
    const result = await callBackend('POST', '/api/analyze/start', {});
    
    if (result) {
      updateStatus('Analysis running...');
      
      // Poll for status with timeout
      pollAnalysisStatus(0);
    }
  });

  async function pollAnalysisStatus(attempts = 0) {
    if (attempts > 30) {
      updateStatus('Analysis timed out');
      return;
    }
    
    const result = await callBackend('GET', '/api/analyze/status');
    
    if (result && result.running) {
      updateStatus(`Analysis: ${result.processed}/${result.total} images`);
      setTimeout(() => pollAnalysisStatus(attempts + 1), 2000);
    } else {
      updateStatus('Analysis complete — check results');
      loadPhotos();
    }
  }

  // --- Navigation ---

  document.querySelectorAll('.nav-item[data-view]').forEach(item => {
    item.addEventListener('click', async () => {
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');

      state.currentView = item.dataset.view;
      state.searchQuery = '';
      elements.searchInput.value = '';
      state.currentPage = 1;

      // Favorites view uses a different endpoint
      if (state.currentView === 'favorites') {
        await loadFavorites();
      } else {
        await loadPhotos();
      }
    });
  });

  // --- Tag Click ---

  document.addEventListener('click', async (e) => {
    const tagItem = e.target.closest('.tag-item');
    if (tagItem) {
      const tag = tagItem.dataset.tag;
      state.searchQuery = tag;
      state.currentPage = 1;
      elements.searchInput.value = tag;
      await loadPhotos();
    }
  });

  // --- Status Updates ---

  function updateStatus(message, type = 'info') {
    elements.statusLeft.textContent = message;
    if (type === 'error') {
      elements.statusLeft.style.color = 'var(--accent)';
    } else {
      elements.statusLeft.style.color = '';
    }
  }

  // --- Initial Load ---

  loadPhotos();
});

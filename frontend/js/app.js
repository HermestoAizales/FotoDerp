/**
 * FotoDerp - Frontend Application
 * 
 * Communicates with the Python backend via Electron IPC.
 * Improved version with Collections support.
 */

document.addEventListener('DOMContentLoaded', () => {
  console.log('[FotoDerp] App started - Enhanced Version');
  
  // State
  const state = {
    currentPage: 1,
    perPage: 50,
    totalPhotos: 0,
    selectedPhoto: null,
    currentView: 'all',
    searchQuery: '',
    selectedTags: [],
    collections: [],
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
    btnCulling: document.getElementById('btn-culling'),
    viewToggle: document.getElementById('view-toggle'),
    tagsList: document.getElementById('tags-list'),
    personsList: document.getElementById('persons-list'),
    collectionsList: document.getElementById('collections-list'),
  };

  // --- Backend Communication ---
  async function callBackend(method, endpoint, data = null) {
    try {
      const result = await window.fotoDerp.backendRequest(method, endpoint, data);
      return result;
    } catch (error) {
      console.error('[FotoDerp] Backend error:', error);
      updateStatus('Backend unreachable', 'error');
      return null;
    }
  }

  // --- Photo Loading ---
  async function loadPhotos() {
    updateStatus('Lade Bilder...');
    
    const params = new URLSearchParams({
      page: state.currentPage,
      per_page: state.perPage,
    });

    // Use search endpoint for text queries
    if (state.searchQuery) {
      params.set('query', state.searchQuery);
    }

    const result = await callBackend('GET', `/api/photos?${params}`);
    
    if (result) {
      const photos = result.photos || [];
      renderPhotos(photos);
      state.totalPhotos = result.total || photos.length;
      updatePagination();
      updatePhotoCount();
    }
  }

  async function renderPhotos(photos) {
    elements.photoGrid.innerHTML = '';
    
    if (photos.length === 0) {
      elements.photoGrid.innerHTML = `
        <div class="photo-placeholder">
          <div class="placeholder-icon">📷</div>
          <span>Keine Bilder importiert</span>
          <p>Klicke auf "Import" um Fotos hinzuzufügen</p>
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
      if (photo.path && window.fotoDerp.imageBlobUrl) {
        const blobUrl = await window.fotoDerp.imageBlobUrl(photo.path);
        if (blobUrl) {
          img.src = blobUrl;
        } else {
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
    updateStatus(`Ausgewählt: ${photo.filename}`);
    
    // Load detail view
    const result = await callBackend('GET', `/api/photos/${photo.id}`);
    
    if (result) {
      renderPreview(result);
    }
  }

  async function renderPreview(photo) {
    // Load image via IPC for local file access
    let imageUrl = '';
    if (photo.path && window.fotoDerp.imageBlobUrl) {
      imageUrl = await window.fotoDerp.imageBlobUrl(photo.path) || '';
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
          `<div class="preview-placeholder">Bild nicht verfügbar</div>`
        }
      </div>
      <div class="preview-meta">
        <h4>${photo.filename}</h4>
        <p>Größe: ${photo.width || '?'}×${photo.height || '?'}</p>
        <p>Format: ${photo.format || 'unbekannt'}</p>
        <p>Aufnahme: ${photo.captured_at || 'Unbekannt'}</p>
        ${photo.gps_lat ? `<p>Position: ${photo.gps_lat}, ${photo.gps_lon}</p>` : ''}
        <p>Status: ${photo.status || 'unbekannt'}</p>

        <h4 style="margin-top: 12px;">Bewertung</h4>
        <div id="star-rating-container"></div>

        <h4 style="margin-top: 12px;">Schlagwörter</h4>
        <div class="preview-tags">
          ${tagsList || '<span style="color: var(--text-secondary)">Keine Tags</span>'}
        </div>

        ${analysesList ? `
          <h4 style="margin-top: 12px;">KI-Analysen</h4>
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
    updateStatus('Lade Favoriten...');

    const params = new URLSearchParams({
      page: state.currentPage,
      per_page: state.perPage,
    });

    const result = await callBackend('GET', `/api/photos/favorites?${params}`);

    if (result) {
      renderPhotos(result.photos || []);
      state.totalPhotos = result.total || 0;
      updatePagination();
      updatePhotoCount();
    }
  }

  // --- Collections Loading ---
  async function loadCollections() {
    updateStatus('Lade Sammlungen...');
    
    const result = await callBackend('GET', '/api/collections');
    
    if (result && result.length > 0) {
      renderCollections(result);
      state.collections = result;
      updateStatus(`${result.length} Sammlungen geladen`);
    } else {
      elements.photoGrid.innerHTML = `
        <div class="photo-placeholder">
          <div class="placeholder-icon">📚</div>
          <span>Keine Sammlungen erstellt</span>
          <button id="btn-create-first-collection" class="btn-primary">Erste Sammlung erstellen</button>
        </div>
      `;
      
      document.getElementById('btn-create-first-collection')?.addEventListener('click', () => {
        createCollection();
      });
      
      updateStatus('Keine Sammlungen');
    }
  }

  function renderCollections(collections) {
    elements.photoGrid.innerHTML = '';
    
    collections.forEach(col => {
      const card = document.createElement('div');
      card.className = 'collection-card';
      
      card.innerHTML = `
        <div class="collection-header">
          <h4>${col.name}</h4>
          <span class="photo-count">${col.photo_count || 0} Bilder</span>
        </div>
        <div class="collection-actions">
          <button class="btn-small" onclick="viewCollection('${col.id}')">Ansehen</button>
          <button class="btn-small btn-danger" onclick="deleteCollection('${col.id}')">Löschen</button>
        </div>
      `;
      
      elements.photoGrid.appendChild(card);
    });
  }

  window.viewCollection = async function(collectionId) {
    updateStatus('Lade Sammlung...');
    // TODO: Load collection photos
    await loadPhotos();
  };

  window.deleteCollection = async function(collectionId) {
    if (!confirm('Sammlung wirklich löschen?')) return;
    
    const result = await callBackend('DELETE', `/api/collections/${collectionId}`);
    if (result) {
      await loadCollections();
    }
  };

  async function createCollection() {
    const name = prompt('Name der Sammlung:');
    if (!name) return;
    
    const result = await callBackend('POST', '/api/collections', { name });
    if (result) {
      await loadCollections();
    }
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
    elements.pageInfo.textContent = `Seite ${state.currentPage} von ${maxPage || 1}`;
    elements.prevPage.disabled = state.currentPage <= 1;
    elements.nextPage.disabled = state.currentPage >= maxPage;
  }

  function updatePhotoCount() {
    document.getElementById('photo-count').textContent = `${state.totalPhotos} Bilder`;
  }

  // --- Import ---
  elements.btnImport.addEventListener('click', async () => {
    const folders = await window.fotoDerp.selectFolder();
    if (folders && folders.length > 0) {
      updateStatus(`Importiere: ${folders.join(', ')}`);
      
      const result = await callBackend('POST', '/api/photos/import', {
        paths: folders,
      });
      
      if (result) {
        updateStatus(`${result.imported} Bilder importiert`);
        loadPhotos();
      }
    }
  });

  // --- Analysis ---
  elements.btnAnalyze.addEventListener('click', async () => {
    updateStatus('Starte KI-Analyse...');
    
    const result = await callBackend('POST', '/api/analyze/start', {});
    
    if (result) {
      updateStatus('Analyse läuft...');
      
      // Poll for status with timeout
      pollAnalysisStatus(0);
    }
  });

  async function pollAnalysisStatus(attempts = 0) {
    if (attempts > 30) {
      updateStatus('Analyse-Timeout');
      return;
    }
    
    const result = await callBackend('GET', '/api/analyze/status');
    
    if (result && result.running) {
      updateStatus(`Analyse: ${result.processed}/${result.total} Bilder`);
      setTimeout(() => pollAnalysisStatus(attempts + 1), 2000);
    } else {
      updateStatus('Analyse abgeschlossen');
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

      // Handle different views
      if (state.currentView === 'favorites') {
        await loadFavorites();
      } else if (state.currentView === 'collections') {
        await loadCollections();
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

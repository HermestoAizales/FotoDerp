/**
 * FotoDerp - Frontend Application
 * 
 * Kommuniziert mit dem Python Backend via Electron IPC
 */

document.addEventListener('DOMContentLoaded', () => {
  console.log('[FotoDerp] App gestartet');
  
  // State
  const state = {
    currentPage: 1,
    perPage: 50,
    totalPhotos: 0,
    selectedPhoto: null,
    currentView: 'all',
    searchQuery: '',
  };

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
  };

  // --- Backend Communication ---

  async function callBackend(method, endpoint, data = null) {
    try {
      const result = await window.fotoerp.backendRequest(method, endpoint, data);
      return result;
    } catch (error) {
      console.error('[FotoDerp] Backend-Fehler:', error);
      updateStatus('Backend nicht erreichbar', 'error');
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

    if (state.searchQuery) {
      params.set('search', state.searchQuery);
    }

    const result = await callBackend('GET', `/api/photos?${params}`);
    
    if (result) {
      renderPhotos(result.photos || []);
      state.totalPhotos = result.total || 0;
      updatePagination();
    }
    
    updateStatus(`${state.totalPhotos} Bilder geladen`);
  }

  function renderPhotos(photos) {
    elements.photoGrid.innerHTML = '';
    
    if (photos.length === 0) {
      elements.photoGrid.innerHTML = `
        <div class="photo-placeholder">
          <div class="placeholder-icon">📷</div>
          <span>Keine Bilder gefunden</span>
        </div>
      `;
      return;
    }

    photos.forEach(photo => {
      const item = document.createElement('div');
      item.className = 'photo-item';
      item.dataset.photoId = photo.id;
      
      // Preview thumbnail
      const img = document.createElement('img');
      img.src = `/api/photos/${photo.id}/preview`;
      img.alt = photo.filename;
      img.loading = 'lazy';
      
      // Overlay mit Tags
      const overlay = document.createElement('div');
      overlay.className = 'photo-overlay';
      overlay.textContent = photo.filename;
      
      item.appendChild(img);
      item.appendChild(overlay);
      item.addEventListener('click', () => selectPhoto(photo));
      
      elements.photoGrid.appendChild(item);
    });
  }

  // --- Photo Selection & Preview ---

  async function selectPhoto(photo) {
    state.selectedPhoto = photo;
    updateStatus(`Ausgewählt: ${photo.filename}`);
    
    // Lade Detail-Ansicht
    const result = await callBackend('GET', `/api/photos/${photo.id}`);
    
    if (result) {
      renderPreview(result);
    }
  }

  function renderPreview(photo) {
    elements.previewPanel.innerHTML = `
      <img src="/api/photos/${photo.id}/preview" alt="${photo.filename}" class="preview-image">
      <div class="preview-meta">
        <h4>${photo.filename}</h4>
        <p>Größe: ${photo.width}×${photo.height}</p>
        <p>Format: ${photo.format}</p>
        <p>Erstellt: ${photo.captured_at || 'Unbekannt'}</p>
        ${photo.gps_lat ? `<p>Ort: ${photo.gps_lat}, ${photo.gps_lon}</p>` : ''}
        
        <h4 style="margin-top: 12px;">KI-Tags</h4>
        <div class="preview-tags">
          ${(photo.tags || []).map(tag => 
            `<span class="preview-tag">${tag.name}</span>`
          ).join('')}
        </div>
        
        ${photo.analysis?.aesthetic_score ? `
          <h4 style="margin-top: 12px;">Ästhetik-Score</h4>
          <p>${(photo.analysis.aesthetic_score * 100).toFixed(0)}%</p>
        ` : ''}
      </div>
    `;
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

  // --- Import ---

  elements.btnImport.addEventListener('click', async () => {
    const folders = await window.fotoerp.selectFolder();
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
      
      // Poll for status
      pollAnalysisStatus();
    }
  });

  async function pollAnalysisStatus() {
    const result = await callBackend('GET', '/api/analyze/status');
    
    if (result && result.running) {
      updateStatus(`Analyse: ${result.processed}/${result.total} Bilder`);
      setTimeout(pollAnalysisStatus, 2000);
    } else {
      updateStatus('Analyse abgeschlossen');
    }
  }

  // --- Navigation ---

  document.querySelectorAll('.nav-item[data-view]').forEach(item => {
    item.addEventListener('click', async () => {
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      
      state.currentView = item.dataset.view;
      state.currentPage = 1;
      await loadPhotos();
    });
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

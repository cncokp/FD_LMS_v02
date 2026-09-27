/**
 * FD-LMS: Main WebGIS Application Coordinator
 * Handles:
 * - Map initialization
 * - CS Plot boundary toggles
 * - Basemap selection
 * - Search autocomplete by Plot # or UID
 * - CSV Export
 */

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initialize Map
  await MapEngine.init();

  // 2. Setup UI controls
  setupThemeSwitcher();
  setupHorizontalWidget();
  setupBasemapSwitcher();
  setupLayerToggles();
  setupSpatialFilter();
  setupSearchAutocomplete();
  setupExportCSV();
  setupHierarchyAndDrillDown();
  setupUserAuth();
});

function setupHorizontalWidget() {
  const tabBtnLayers = document.getElementById('tabBtnLayers');
  const tabBtnFilter = document.getElementById('tabBtnFilter');
  const dropdownPanel = document.getElementById('dropdownPanel');
  const panelHeaderTitle = document.getElementById('panelHeaderTitle');
  const viewLayers = document.getElementById('viewLayers');
  const viewFilter = document.getElementById('viewFilter');
  const btnCloseDropdownPanel = document.getElementById('btnCloseDropdownPanel');
  const btnCloseDossier = document.getElementById('btnCloseDossier');

  let currentTab = 'filter';

  window.switchPanelTab = function(tab) {
    currentTab = tab;
    if (window.closeSearchWidget) window.closeSearchWidget();
    if (dropdownPanel) dropdownPanel.classList.remove('collapsed');

    if (tabBtnLayers) tabBtnLayers.classList.remove('active');
    if (tabBtnFilter) tabBtnFilter.classList.remove('active');

    if (viewLayers) viewLayers.classList.add('hidden');
    if (viewFilter) viewFilter.classList.add('hidden');

    if (tab === 'layers') {
      if (tabBtnLayers) tabBtnLayers.classList.add('active');
      if (panelHeaderTitle) panelHeaderTitle.innerHTML = '<i class="fa-solid fa-layer-group"></i> Cadastral Layers';
      if (viewLayers) viewLayers.classList.remove('hidden');
    } else if (tab === 'filter') {
      if (tabBtnFilter) tabBtnFilter.classList.add('active');
      if (panelHeaderTitle) panelHeaderTitle.innerHTML = '<i class="fa-solid fa-filter"></i> Spatial Filter & Drill-Down';
      if (viewFilter) viewFilter.classList.remove('hidden');
    }
  };

  window.openLayersPanel = function(tab = 'filter') {
    window.switchPanelTab(tab);
  };

  window.closeLayersPanel = function() {
    if (dropdownPanel) dropdownPanel.classList.add('collapsed');
    if (tabBtnLayers) tabBtnLayers.classList.remove('active');
    if (tabBtnFilter) tabBtnFilter.classList.remove('active');
  };

  window.isLayersPanelOpen = function() {
    return dropdownPanel && !dropdownPanel.classList.contains('collapsed');
  };

  if (tabBtnLayers) {
    tabBtnLayers.addEventListener('click', () => {
      if (window.isLayersPanelOpen() && currentTab === 'layers') {
        window.closeLayersPanel();
      } else {
        window.switchPanelTab('layers');
      }
    });
  }

  if (tabBtnFilter) {
    tabBtnFilter.addEventListener('click', () => {
      if (window.isLayersPanelOpen() && currentTab === 'filter') {
        window.closeLayersPanel();
      } else {
        window.switchPanelTab('filter');
      }
    });
  }

  if (btnCloseDropdownPanel) {
    btnCloseDropdownPanel.addEventListener('click', () => {
      window.closeLayersPanel();
    });
  }

  if (btnCloseDossier) {
    btnCloseDossier.addEventListener('click', () => {
      if (typeof Dossier !== 'undefined') Dossier.close();
      MapEngine.clearHighlight();
    });
  }
}

function setupBasemapSwitcher() {
  const toggleBtn = document.getElementById('btnBasemapToggle');
  const popup = document.getElementById('basemapPickerPopup');
  const items = document.querySelectorAll('.basemap-picker-item');
  const btnZoomIn = document.getElementById('btnZoomIn');
  const btnZoomOut = document.getElementById('btnZoomOut');

  if (toggleBtn && popup) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isHidden = popup.classList.contains('hidden');
      if (isHidden) {
        popup.classList.remove('hidden');
        popup.style.display = 'flex';
        toggleBtn.classList.add('active');
      } else {
        popup.classList.add('hidden');
        popup.style.display = 'none';
        toggleBtn.classList.remove('active');
      }
    });

    document.addEventListener('click', (e) => {
      if (!popup.contains(e.target) && e.target !== toggleBtn && !toggleBtn.contains(e.target)) {
        popup.classList.add('hidden');
        popup.style.display = 'none';
        toggleBtn.classList.remove('active');
      }
    });
  }

  items.forEach(item => {
    item.addEventListener('click', (e) => {
      e.stopPropagation();
      items.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      const basemap = item.dataset.basemap;
      MapEngine.setBasemap(basemap);
      if (popup) {
        popup.classList.add('hidden');
        popup.style.display = 'none';
      }
      if (toggleBtn) {
        toggleBtn.classList.remove('active');
      }
    });
  });

  if (btnZoomIn) {
    btnZoomIn.addEventListener('click', () => {
      if (MapEngine.map) MapEngine.map.zoomIn();
    });
  }

  if (btnZoomOut) {
    btnZoomOut.addEventListener('click', () => {
      if (MapEngine.map) MapEngine.map.zoomOut();
    });
  }

  const btnDefaultExtent = document.getElementById('btnDefaultExtent');
  if (btnDefaultExtent) {
    btnDefaultExtent.addEventListener('click', () => {
      MapEngine.resetToDefaultExtent();
    });
  }
}

function setupLayerToggles() {
  const toggleAllPlots = document.getElementById('toggleAllPlots');
  if (toggleAllPlots) {
    toggleAllPlots.addEventListener('change', (e) => {
      MapEngine.toggleAllPlots(e.target.checked);
    });
  }

  const toggleForestPlots = document.getElementById('toggleForestPlots');
  if (toggleForestPlots) {
    toggleForestPlots.addEventListener('change', (e) => {
      MapEngine.toggleForestPlots(e.target.checked);
    });
  }

  const toggleRsPlots = document.getElementById('toggleRsPlots');
  if (toggleRsPlots) {
    toggleRsPlots.addEventListener('change', (e) => {
      MapEngine.toggleRsPlots(e.target.checked);
    });
  }

  const toggleRangeBoundaries = document.getElementById('toggleRangeBoundaries');
  if (toggleRangeBoundaries) {
    toggleRangeBoundaries.addEventListener('change', (e) => {
      MapEngine.toggleRangeBoundaries(e.target.checked);
    });
  }

  const toggleBeatBoundaries = document.getElementById('toggleBeatBoundaries');
  if (toggleBeatBoundaries) {
    toggleBeatBoundaries.addEventListener('change', (e) => {
      MapEngine.toggleBeatBoundaries(e.target.checked);
    });
  }

  const toggleCSPlots = document.getElementById('toggleCSPlots');
  if (toggleCSPlots) {
    toggleCSPlots.addEventListener('change', (e) => {
      MapEngine.toggleCSPlots(e.target.checked);
    });
  }

  const toggleEncroachments = document.getElementById('toggleEncroachments');
  if (toggleEncroachments) {
    toggleEncroachments.addEventListener('change', (e) => {
      MapEngine.toggleEncroachments(e.target.checked);
    });
  }

  const btnQuickEncroach = document.getElementById('btnQuickEncroach');
  if (btnQuickEncroach) {
    btnQuickEncroach.addEventListener('click', () => {
      MapEngine.focusEncroachments();
    });
  }
}

function setupSpatialFilter() {
  const divisionSelect = document.getElementById('filterDivisionSelect');
  const rangeSelect = document.getElementById('filterRangeSelect');
  const beatSelect = document.getElementById('filterBeatSelect');
  const mouzaSelect = document.getElementById('filterMouzaSelect');
  const plotInput = document.getElementById('filterPlotInput');
  const plotList = document.getElementById('filterPlotList');
  const statusBox = document.getElementById('filterStatusBox');
  const statusText = document.getElementById('filterStatusText');
  const btnClearMini = document.getElementById('btnClearFilterMini');
  const btnApply = document.getElementById('btnApplyFilter');
  const btnReset = document.getElementById('btnResetFilter');
  const filterDot = document.getElementById('tabFilterDot');

  if (!btnApply || !beatSelect || !mouzaSelect) return;

  const rangeBeatMap = {
    'National Park Range': ['Park Beat', 'Bankhoira Beat', 'Baupara Beat'],
    'Bhawal Range': ['BK Bari Beat', 'Rajendrapur West Beat', 'Baruipara Beat', 'Bhabanipur Beat']
  };

  const allBeats = [
    'Park Beat',
    'Bankhoira Beat',
    'Baupara Beat',
    'BK Bari Beat',
    'Rajendrapur West Beat',
    'Baruipara Beat',
    'Bhabanipur Beat'
  ];

  const beatMouzaMap = {
    'Park Beat': ['Araishprashad', 'Barui Para'],
    'Bankhoira': ['Bankhoira'],
    'Bankhoira Beat': ['Bankhoira'],
    'Baruipara': ['Barui Para'],
    'Baruipara Beat': ['Barui Para'],
    'Rajendrapur West': ['Barui Para'],
    'Rajendrapur West Beat': ['Barui Para'],
    'BK Bari': ['B K Bari'],
    'BK Bari Beat': ['B K Bari'],
    'Bhabanipur': ['Barui Para', 'Mahona Bhabanipur'],
    'Bhabanipur Beat': ['Barui Para', 'Mahona Bhabanipur'],
    'Baupara': ['Araishprashad', 'Bahadurpur', 'Baupara', 'Uttar Salna'],
    'Baupara Beat': ['Araishprashad', 'Bahadurpur', 'Baupara', 'Uttar Salna']
  };

  const allMouzas = [
    'Araishprashad',
    'B K Bari',
    'Bahadurpur',
    'Bankhoira',
    'Barui Para',
    'Baupara',
    'Mahona Bhabanipur',
    'Uttar Salna'
  ];

  function updateBeatOptions(selectedRange) {
    const currentVal = beatSelect.value;
    beatSelect.innerHTML = '<option value="">All Beats (Range Overview)</option>';
    const beatsToDisplay = (selectedRange && rangeBeatMap[selectedRange]) ? rangeBeatMap[selectedRange] : allBeats;
    beatsToDisplay.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b;
      opt.textContent = b;
      beatSelect.appendChild(opt);
    });
    if (currentVal && beatsToDisplay.includes(currentVal)) {
      beatSelect.value = currentVal;
    } else {
      beatSelect.value = '';
    }
  }

  function updateMouzaOptions(selectedBeat) {
    const currentVal = mouzaSelect.value;
    mouzaSelect.innerHTML = '<option value="">All Mouzas</option>';
    
    let validMouzas = allMouzas;
    if (selectedBeat && beatMouzaMap[selectedBeat]) {
      validMouzas = beatMouzaMap[selectedBeat];
    }

    validMouzas.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      mouzaSelect.appendChild(opt);
    });

    if (currentVal && validMouzas.includes(currentVal)) {
      mouzaSelect.value = currentVal;
    } else {
      mouzaSelect.value = '';
    }
  }

  function updatePlotDatalist() {
    if (!plotList) return;
    const selectedBeat = beatSelect.value.trim();
    const selectedMouza = mouzaSelect.value.trim();

    const isRsMode = Boolean(MapEngine.isRsPlotsVisible && !MapEngine.isAllPlotsVisible);
    const features = isRsMode
      ? (MapEngine.currentRSFeatures || (MapEngine.rawRSData && MapEngine.rawRSData.features) || [])
      : (MapEngine.currentCSFeatures || (MapEngine.rawCSData && MapEngine.rawCSData.features) || []);
    if (!features.length) return;

    const norm = (s) => (s || '').trim().toLowerCase().replace(/\s+/g, ' ');
    const targetBeat = selectedBeat ? norm(selectedBeat).replace(/\s*beat$/i, '') : '';
    const targetMouza = selectedMouza ? norm(selectedMouza) : '';

    const plotNos = new Set();
    for (let i = 0; i < features.length; i++) {
      const p = features[i].properties || {};
      if (targetBeat) {
        const pBeat = norm(p.beat_name || '').replace(/\s*beat$/i, '');
        if (pBeat !== targetBeat) continue;
      }
      if (targetMouza) {
        const pMouza = norm(p.mouza || '');
        if (pMouza !== targetMouza) continue;
      }
      if (p.plot_no) {
        plotNos.add(String(p.plot_no).trim());
      }
    }

    const sorted = Array.from(plotNos).sort((a, b) => {
      const numA = parseInt(a, 10);
      const numB = parseInt(b, 10);
      if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
      return a.localeCompare(b);
    });

    plotList.innerHTML = sorted.slice(0, 1000).map(p => `<option value="${p}">Plot #${p}</option>`).join('');
  }

  if (divisionSelect) {
    divisionSelect.addEventListener('change', () => {
      if (rangeSelect) rangeSelect.value = '';
      updateBeatOptions('');
      updateMouzaOptions('');
      updatePlotDatalist();
      if (window.AppDrillDown) {
        window.AppDrillDown('division', divisionSelect.value);
      }
    });
  }

  if (rangeSelect) {
    rangeSelect.addEventListener('change', () => {
      const rVal = rangeSelect.value.trim();
      updateBeatOptions(rVal);
      updateMouzaOptions('');
      updatePlotDatalist();
      if (window.AppDrillDown) {
        if (rVal) {
          window.AppDrillDown('range', rVal);
        } else {
          window.AppDrillDown('division', divisionSelect ? divisionSelect.value : 'Bhawal National Park');
        }
      }
    });
  }

  beatSelect.addEventListener('change', () => {
    const bVal = beatSelect.value.trim();
    updateMouzaOptions(bVal);
    updatePlotDatalist();
    if (window.AppDrillDown) {
      if (bVal) {
        window.AppDrillDown('beat', bVal);
      } else if (rangeSelect && rangeSelect.value.trim()) {
        window.AppDrillDown('range', rangeSelect.value.trim());
      } else {
        window.AppDrillDown('division', divisionSelect ? divisionSelect.value : 'Bhawal National Park');
      }
    }
  });

  mouzaSelect.addEventListener('change', () => {
    updatePlotDatalist();
  });

  setTimeout(updatePlotDatalist, 1500);

  function executeFilter() {
    const beat = beatSelect.value.trim();
    const mouza = mouzaSelect.value.trim();
    const plotNo = plotInput.value.trim();

    if (!beat && !mouza && !plotNo) {
      if (statusBox) {
        statusBox.classList.remove('hidden');
        statusBox.classList.add('error');
        if (statusText) statusText.textContent = 'Please select a Beat, Mouza, or Plot #';
      }
      return;
    }

    const res = MapEngine.applyFilter({ beat, mouza, plotNo });

    if (res.count > 0) {
      if (statusBox) {
        statusBox.classList.remove('hidden', 'error');
        let detailParts = [];
        if (beat) detailParts.push(beat.endsWith('Beat') ? beat : `${beat} Beat`);
        if (mouza) detailParts.push(mouza);
        if (plotNo) detailParts.push(`Plot #${plotNo}`);
        const labelStr = detailParts.join(' • ');
        if (statusText) {
          statusText.textContent = res.count === 1 ? `Plot #${res.matches[0].properties.plot_no} Found (${res.matches[0].properties.mouza || ''})` : `${res.count} Plots Found (${labelStr})`;
        }
      }
      if (filterDot) filterDot.classList.remove('hidden');
    } else if (res.beatOnly) {
      if (statusBox) {
        statusBox.classList.remove('hidden', 'error');
        if (statusText) statusText.textContent = `Zoomed to ${res.beatName} Boundary`;
      }
      if (filterDot) filterDot.classList.remove('hidden');
    } else {
      if (statusBox) {
        statusBox.classList.remove('hidden');
        statusBox.classList.add('error');
        if (statusText) statusText.textContent = 'No matching parcels found';
      }
      if (filterDot) filterDot.classList.add('hidden');
    }
  }

  btnApply.addEventListener('click', executeFilter);

  plotInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      executeFilter();
    }
  });

  function resetFilter() {
    if (divisionSelect) divisionSelect.value = 'Biodiversity Conservation Division';
    if (rangeSelect) rangeSelect.value = '';
    updateBeatOptions('');
    beatSelect.value = '';
    updateMouzaOptions('');
    mouzaSelect.value = '';
    plotInput.value = '';
    updatePlotDatalist();

    MapEngine.clearFilter();

    if (window.AppDrillDown) {
      window.AppDrillDown('division', 'Bhawal National Park');
    }

    if (statusBox) {
      statusBox.classList.add('hidden');
      statusBox.classList.remove('error');
    }
    if (filterDot) {
      filterDot.classList.add('hidden');
    }
  }

  btnReset.addEventListener('click', resetFilter);
  if (btnClearMini) {
    btnClearMini.addEventListener('click', resetFilter);
  }
}

function setupSearchAutocomplete() {
  const container = document.getElementById('expandableSearchContainer');
  const toggleBtn = document.getElementById('btnToggleSearch');
  const input = document.getElementById('searchInput');
  const dropdown = document.getElementById('searchResults');
  const btnClear = document.getElementById('btnClearSearch');
  if (!input || !dropdown) return;

  let searchTimeout = null;

  function collapseSearch() {
    dropdown.classList.add('hidden');
    dropdown.style.display = 'none';
    dropdown.innerHTML = '';
  }

  function expandSearch() {
    if (container) container.classList.add('expanded');
    if (toggleBtn) toggleBtn.classList.add('active');
    // Collapse Layers panel when search expands
    if (window.closeLayersPanel) window.closeLayersPanel();
    setTimeout(() => input.focus(), 50);
  }

  function closeSearch() {
    if (container) container.classList.remove('expanded');
    if (toggleBtn) toggleBtn.classList.remove('active');
    collapseSearch();
  }

  window.closeSearchWidget = function() {
    closeSearch();
  };

  if (toggleBtn) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isExpanded = container && container.classList.contains('expanded');
      if (isExpanded) {
        closeSearch();
        // If closing search and layers panel is closed, restore layers panel
        if (window.openLayersPanel && !window.isLayersPanelOpen()) {
          window.openLayersPanel();
        }
      } else {
        expandSearch();
      }
    });
  }

  if (btnClear) {
    btnClear.addEventListener('click', (e) => {
      e.stopPropagation();
      input.value = '';
      btnClear.classList.add('hidden');
      collapseSearch();
      input.focus();
    });
  }

  input.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    const q = input.value.trim();

    if (btnClear) {
      if (q.length > 0) {
        btnClear.classList.remove('hidden');
      } else {
        btnClear.classList.add('hidden');
      }
    }

    if (q.length === 0) {
      collapseSearch();
      return;
    }

    searchTimeout = setTimeout(async () => {
      try {
        const qLower = q.toLowerCase();

        // 1. In-memory Beat Boundary search
        const beatMatches = [];
        if (MapEngine.rawBeatData && MapEngine.rawBeatData.features) {
          for (const feat of MapEngine.rawBeatData.features) {
            const p = feat.properties || {};
            const bName = (p.beat_name || '').toLowerCase();
            const rName = (p.raw_name || '').toLowerCase();
            if (bName.includes(qLower) || rName.includes(qLower) || (qLower.includes('beat') && (bName || rName))) {
              beatMatches.push({
                type: 'beat',
                id: p.id,
                label: p.beat_name,
                sublabel: `${p.area_acre ? Number(p.area_acre).toLocaleString() + ' Acres' : 'Forest Beat'} • Administrative Boundary`,
                lat: p.center_lat,
                lng: p.center_lng,
                bounds: p.bounds
              });
            }
          }
        }

        // 2. Server Plot & Mouza search
        let serverResults = [];
        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
          if (res.ok) {
            serverResults = await res.json();
          }
        } catch (fetchErr) {
          console.warn("Search fetch error:", fetchErr);
        }

        const combined = [...beatMatches, ...serverResults];

        if (combined.length === 0) {
          dropdown.innerHTML = `<div class="search-item" style="color: var(--text-dim); font-size: 11.5px; padding: 10px 12px; pointer-events: none;"><i class="fa-solid fa-circle-exclamation" style="margin-right: 6px;"></i>No matching plot, mouza, or beat found</div>`;
          dropdown.classList.remove('hidden');
          dropdown.style.display = 'flex';
          return;
        }

        dropdown.innerHTML = combined.map((item, idx) => {
          const boundsAttr = JSON.stringify(item.bounds || []);
          let badgeClass = 'badge-plot';
          let badgeText = 'PLOT';
          let iconClass = 'fa-solid fa-scroll';
          let iconColor = '#34d399';

          if (item.type === 'beat') {
            badgeClass = 'badge-beat';
            badgeText = 'BEAT';
            iconClass = 'fa-solid fa-tree-city';
            iconColor = '#38bdf8';
          } else if (item.type === 'mouza') {
            badgeClass = 'badge-mouza';
            badgeText = 'MOUZA';
            iconClass = 'fa-solid fa-map-location-dot';
            iconColor = '#c084fc';
          }

          return `
            <div class="search-item ${idx === 0 ? 'selected' : ''}" data-index="${idx}" data-type="${item.type}" data-id="${item.id || ''}" data-lat="${item.lat}" data-lng="${item.lng}" data-bounds='${boundsAttr}'>
              <div class="search-item-header">
                <div class="search-item-label">
                  <i class="${iconClass}" style="color: ${iconColor};"></i>
                  <span>${item.label}</span>
                </div>
                <span class="search-badge ${badgeClass}">${badgeText}</span>
              </div>
              <div class="search-item-sublabel">${item.sublabel}</div>
            </div>
          `;
        }).join('');

        dropdown.classList.remove('hidden');
        dropdown.style.display = 'flex';

        dropdown.querySelectorAll('.search-item').forEach(el => {
          el.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = el.dataset.id;
            const type = el.dataset.type;
            const lat = parseFloat(el.dataset.lat);
            const lng = parseFloat(el.dataset.lng);
            let bounds = null;
            try {
              bounds = JSON.parse(el.dataset.bounds || 'null');
            } catch (err) {}

            collapseSearch();
            input.value = '';
            if (btnClear) btnClear.classList.add('hidden');
            input.blur();

            if (type === 'beat') {
              MapEngine.flyToBeat({ id, lat, lng, bounds });
            } else if (id && (type === 'cs_plot' || type === 'rs_plot' || type === 'plot')) {
              const activeType = (MapEngine.isRsPlotsVisible && !MapEngine.isAllPlotsVisible) ? 'rs_plot' : (type || 'cs_plot');
              MapEngine.selectPlotById(activeType, id, (lat && lng) ? [lat, lng] : null, bounds);
            } else if (lat && lng) {
              MapEngine.map.panTo([lat, lng], { animate: true });
            }
          });

          el.addEventListener('mouseenter', () => {
            dropdown.querySelectorAll('.search-item').forEach(it => it.classList.remove('selected'));
            el.classList.add('selected');
          });
        });

      } catch (err) {
        console.error("Search error:", err);
      }
    }, 150);
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      collapseSearch();
      if (!input.value) {
        closeSearch();
      }
      input.blur();
      return;
    }

    const items = Array.from(dropdown.querySelectorAll('.search-item'));
    if (items.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      let curr = items.findIndex(el => el.classList.contains('selected'));
      if (curr >= 0) items[curr].classList.remove('selected');
      curr = (curr + 1) % items.length;
      items[curr].classList.add('selected');
      items[curr].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      let curr = items.findIndex(el => el.classList.contains('selected'));
      if (curr >= 0) items[curr].classList.remove('selected');
      curr = (curr - 1 + items.length) % items.length;
      items[curr].classList.add('selected');
      items[curr].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const selected = dropdown.querySelector('.search-item.selected') || items[0];
      if (selected) {
        selected.click();
      }
    }
  });

  document.addEventListener('click', (e) => {
    if (container && !container.contains(e.target)) {
      collapseSearch();
      if (!input.value.trim()) {
        closeSearch();
      }
    }
  });
}

function setupExportCSV() {
  const btnExport = document.getElementById('btnExport');
  if (!btnExport) return;

  btnExport.addEventListener('click', () => {
    window.location.href = `/api/export/csv`;
  });
}

function setupThemeSwitcher() {
  const btnThemeToggle = document.getElementById('btnThemeToggle');
  if (!btnThemeToggle) return;

  const STORAGE_KEY = 'fd_lms_theme_v2';

  const getStoredTheme = () => {
    try {
      return localStorage.getItem(STORAGE_KEY) || 'light';
    } catch (e) {
      return 'light';
    }
  };

  const applyTheme = (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {}

    const isLight = theme === 'light';
    btnThemeToggle.setAttribute('title', isLight ? 'Switch to Dark Theme' : 'Switch to Light Theme');
    btnThemeToggle.setAttribute('aria-label', isLight ? 'Switch to Dark Theme' : 'Switch to Light Theme');
  };

  // Sync state on load (defaults to light)
  applyTheme(getStoredTheme());

  btnThemeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(nextTheme);
  });
}

function setupHierarchyAndDrillDown() {
  const treeContainer = document.getElementById('hierarchyTreeList');
  const btnResetToDivision = document.getElementById('btnResetToDivision');
  const kpiBadge = document.getElementById('kpiLevelBadge');
  const kpiTitle = document.getElementById('kpiTitle');
  const kpiSubtitle = document.getElementById('kpiSubtitle');
  const kpiArea = document.getElementById('kpiArea');
  const kpiForestParcels = document.getElementById('kpiForestParcels');
  const kpiCadastralPlots = document.getElementById('kpiCadastralPlots');
  const kpiEncroachments = document.getElementById('kpiEncroachments');

  const bcDivision = document.getElementById('bcDivision');
  const bcSepRange = document.getElementById('bcSepRange');
  const bcRange = document.getElementById('bcRange');
  const bcSepBeat = document.getElementById('bcSepBeat');
  const bcBeat = document.getElementById('bcBeat');

  const jurisdictionModal = document.getElementById('jurisdictionModal');
  const btnOpenJurisdictionModal = document.getElementById('btnOpenJurisdictionModal');
  const btnCloseJurisdictionModal = document.getElementById('btnCloseJurisdictionModal');

  const cardDrillDivision = document.getElementById('cardDrillDivision');
  const cardDrillRangeNP = document.getElementById('cardDrillRangeNP');
  const cardDrillRangeBhawal = document.getElementById('cardDrillRangeBhawal');
  const beatPills = document.querySelectorAll('.beat-pill-btn');

  let hierarchyTree = null;
  let currentJurisdiction = {
    level: 'division',
    name: 'Bhawal National Park',
    range: null,
    beat: null
  };

  const fmt = (n) => (n != null ? Number(n).toLocaleString() : '—');

  function updateBreadcrumbs() {
    if (!bcDivision) return;
    if (currentJurisdiction.level === 'division') {
      bcDivision.classList.add('active');
      if (bcSepRange) bcSepRange.style.display = 'none';
      if (bcRange) bcRange.style.display = 'none';
      if (bcSepBeat) bcSepBeat.style.display = 'none';
      if (bcBeat) bcBeat.style.display = 'none';
    } else if (currentJurisdiction.level === 'range') {
      bcDivision.classList.remove('active');
      if (bcSepRange) bcSepRange.style.display = 'inline';
      if (bcRange) {
        bcRange.style.display = 'inline-flex';
        bcRange.textContent = currentJurisdiction.range;
        bcRange.classList.add('active');
      }
      if (bcSepBeat) bcSepBeat.style.display = 'none';
      if (bcBeat) bcBeat.style.display = 'none';
    } else if (currentJurisdiction.level === 'beat') {
      bcDivision.classList.remove('active');
      if (bcSepRange) bcSepRange.style.display = 'inline';
      if (bcRange) {
        bcRange.style.display = 'inline-flex';
        bcRange.textContent = currentJurisdiction.range || 'Range';
        bcRange.classList.remove('active');
      }
      if (bcSepBeat) bcSepBeat.style.display = 'inline';
      if (bcBeat) {
        bcBeat.style.display = 'inline-flex';
        bcBeat.textContent = currentJurisdiction.beat;
        bcBeat.classList.add('active');
      }
    }
  }

  function updateKPI(level, itemData, parentName) {
    if (!kpiTitle || !itemData) return;
    if (level === 'division') {
      if (kpiBadge) kpiBadge.textContent = 'Division Level';
      kpiTitle.textContent = itemData.display_name || itemData.name || 'Bhawal National Park';
      if (kpiSubtitle) kpiSubtitle.textContent = 'Biodiversity Conservation Division';
      if (kpiArea) kpiArea.textContent = fmt(Math.round(itemData.area_acre || 24718));
      if (kpiForestParcels) kpiForestParcels.textContent = fmt(itemData.forest_plots_count || 3518);
      if (kpiCadastralPlots) kpiCadastralPlots.textContent = fmt(itemData.cadastral_plots_count || 19463);
      if (kpiEncroachments) kpiEncroachments.textContent = fmt(itemData.encroachments_count || 41);
    } else if (level === 'range') {
      if (kpiBadge) kpiBadge.textContent = 'Range Level';
      kpiTitle.textContent = itemData.name;
      if (kpiSubtitle) kpiSubtitle.textContent = 'Bhawal National Park • Division Scope';
      if (kpiArea) kpiArea.textContent = fmt(Math.round(itemData.area_acre));
      if (kpiForestParcels) kpiForestParcels.textContent = fmt(itemData.forest_plots_count || (itemData.name.includes('National Park') ? 1412 : 2106));
      if (kpiCadastralPlots) kpiCadastralPlots.textContent = fmt(itemData.cadastral_plots_count || (itemData.name.includes('National Park') ? 7820 : 11643));
      if (kpiEncroachments) kpiEncroachments.textContent = fmt(itemData.encroachments_count || (itemData.name.includes('National Park') ? 19 : 22));
    } else if (level === 'beat') {
      if (kpiBadge) kpiBadge.textContent = 'Beat Level';
      kpiTitle.textContent = itemData.name;
      if (kpiSubtitle) kpiSubtitle.textContent = `${parentName || 'Forest Range'} • Cadastral Parcels`;
      if (kpiArea) kpiArea.textContent = fmt(Math.round(itemData.area_acre || 3500));
      if (kpiForestParcels) kpiForestParcels.textContent = fmt(itemData.forest_plots_count || Math.round((itemData.area_acre || 3500) * 0.15));
      if (kpiCadastralPlots) kpiCadastralPlots.textContent = fmt(itemData.cadastral_plots_count || Math.round((itemData.area_acre || 3500) * 0.85));
      if (kpiEncroachments) kpiEncroachments.textContent = fmt(itemData.encroachments_count || 6);
    }
  }

  function highlightActiveTreeNode() {
    if (!treeContainer) return;
    treeContainer.querySelectorAll('.tree-node-row').forEach(row => row.classList.remove('active'));
    const targetName = (currentJurisdiction.name || '').toLowerCase();
    const rows = treeContainer.querySelectorAll('.tree-node-row');
    for (const r of rows) {
      const node = r.closest('.tree-node');
      const nName = (node && node.dataset.name || '').toLowerCase();
      if (nName === targetName || (currentJurisdiction.level === 'division' && node && node.dataset.level === 'division')) {
        r.classList.add('active');
        break;
      }
    }
  }

  window.AppDrillDown = function(level, name) {
    if (!hierarchyTree) return;

    if (level === 'division') {
      currentJurisdiction = {
        level: 'division',
        name: 'Bhawal National Park',
        range: null,
        beat: null
      };
      updateKPI('division', hierarchyTree);
      const divSel = document.getElementById('filterDivisionSelect');
      if (divSel) divSel.value = 'Biodiversity Conservation Division';
      const rngSel = document.getElementById('filterRangeSelect');
      if (rngSel) rngSel.value = '';
      const beatSel = document.getElementById('filterBeatSelect');
      if (beatSel) beatSel.value = '';
      const mouzaSel = document.getElementById('filterMouzaSelect');
      if (mouzaSel) mouzaSel.value = '';
    } else if (level === 'range') {
      const target = (name || '').toLowerCase();
      const rObj = hierarchyTree.ranges.find(r => r.name.toLowerCase().includes(target) || target.includes(r.name.toLowerCase()));
      currentJurisdiction = {
        level: 'range',
        name: rObj ? rObj.name : name,
        range: rObj ? rObj.name : name,
        beat: null
      };
      updateKPI('range', rObj || { name, area_acre: 10000 });
      const rngSel = document.getElementById('filterRangeSelect');
      if (rngSel) rngSel.value = currentJurisdiction.name;
      const beatSel = document.getElementById('filterBeatSelect');
      if (beatSel) beatSel.value = '';
      const mouzaSel = document.getElementById('filterMouzaSelect');
      if (mouzaSel) mouzaSel.value = '';
    } else if (level === 'beat') {
      const norm = s => (s || '').trim().toLowerCase().replace(/\s*beat$/i, '');
      const target = norm(name);
      let foundBeat = null;
      let parentRange = null;

      for (const r of hierarchyTree.ranges) {
        const b = r.beats.find(beat => norm(beat.name) === target);
        if (b) {
          foundBeat = b;
          parentRange = r.name;
          break;
        }
      }

      const defaultRange = ['Park Beat', 'Bankhoira Beat', 'Baupara Beat'].some(b => norm(b) === target)
        ? 'National Park Range'
        : 'Bhawal Range';

      currentJurisdiction = {
        level: 'beat',
        name: foundBeat ? foundBeat.name : (name.endsWith('Beat') ? name : `${name} Beat`),
        range: parentRange || defaultRange,
        beat: foundBeat ? foundBeat.name : (name.endsWith('Beat') ? name : `${name} Beat`)
      };
      updateKPI('beat', foundBeat || { name: currentJurisdiction.beat, area_acre: 3200 }, currentJurisdiction.range);

      const rngSel = document.getElementById('filterRangeSelect');
      if (rngSel && currentJurisdiction.range) {
        rngSel.value = currentJurisdiction.range;
      }
      const filterBeatSelect = document.getElementById('filterBeatSelect');
      if (filterBeatSelect) {
        for (let opt of filterBeatSelect.options) {
          if (norm(opt.value) === target) {
            filterBeatSelect.value = opt.value;
            break;
          }
        }
      }
    }

    updateBreadcrumbs();
    highlightActiveTreeNode();
    MapEngine.setJurisdiction(level, currentJurisdiction.name);
    try {
      sessionStorage.setItem('fd_lms_jurisdiction', JSON.stringify(currentJurisdiction));
    } catch (e) {}
  };

  function renderTree(tree) {
    if (!treeContainer) return;
    let html = `
      <div class="tree-node tree-division" data-level="division" data-name="Bhawal National Park">
        <div class="tree-node-row active">
          <i class="fa-solid fa-sitemap tree-icon tree-icon-division"></i>
          <span class="tree-node-title">${tree.display_name || 'Bhawal National Park'}</span>
          <span class="tree-badge">Division</span>
        </div>
        <div class="tree-children">
    `;

    for (const range of tree.ranges) {
      const isNP = range.name.includes('National Park');
      html += `
        <div class="tree-node tree-range" data-level="range" data-name="${range.name}">
          <div class="tree-node-row">
            <i class="fa-solid fa-compass tree-icon ${isNP ? 'tree-icon-np' : 'tree-icon-bhawal'}"></i>
            <span class="tree-node-title">${range.name}</span>
            <span class="tree-badge">${fmt(Math.round(range.area_acre))} Ac</span>
          </div>
          <div class="tree-children">
      `;
      for (const beat of range.beats) {
        html += `
          <div class="tree-node tree-beat" data-level="beat" data-name="${beat.name}" data-range="${range.name}">
            <div class="tree-node-row">
              <i class="fa-solid fa-tree tree-icon tree-icon-beat"></i>
              <span class="tree-node-title">${beat.name}</span>
              <span class="tree-badge">${fmt(Math.round(beat.area_acre))} Ac</span>
            </div>
          </div>
        `;
      }
      html += `
          </div>
        </div>
      `;
    }

    html += `
        </div>
      </div>
    `;

    treeContainer.innerHTML = html;

    treeContainer.querySelectorAll('.tree-node-row').forEach(row => {
      row.addEventListener('click', (e) => {
        e.stopPropagation();
        const node = row.closest('.tree-node');
        if (!node) return;
        const level = node.dataset.level;
        const name = node.dataset.name;
        window.AppDrillDown(level, name);
      });
    });
  }

  fetch('/api/hierarchy/tree')
    .then(r => r.json())
    .then(tree => {
      hierarchyTree = tree;
      renderTree(tree);
      updateKPI('division', tree);

      const saved = sessionStorage.getItem('fd_lms_jurisdiction');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          window.AppDrillDown(parsed.level, parsed.name);
        } catch (e) {}
      } else {
        const prompted = sessionStorage.getItem('fd_lms_prompted');
        if (!prompted && jurisdictionModal) {
          sessionStorage.setItem('fd_lms_prompted', '1');
          jurisdictionModal.style.display = 'flex';
        }
      }
    })
    .catch(err => {
      console.warn('Failed to load hierarchy tree:', err);
    });

  if (btnOpenJurisdictionModal && jurisdictionModal) {
    btnOpenJurisdictionModal.addEventListener('click', () => {
      jurisdictionModal.style.display = 'flex';
    });
  }

  if (btnCloseJurisdictionModal && jurisdictionModal) {
    btnCloseJurisdictionModal.addEventListener('click', () => {
      jurisdictionModal.style.display = 'none';
    });
  }

  if (cardDrillDivision && jurisdictionModal) {
    cardDrillDivision.addEventListener('click', () => {
      jurisdictionModal.style.display = 'none';
      window.AppDrillDown('division', 'Bhawal National Park');
    });
  }

  if (cardDrillRangeNP && jurisdictionModal) {
    cardDrillRangeNP.addEventListener('click', () => {
      jurisdictionModal.style.display = 'none';
      window.AppDrillDown('range', 'National Park Range');
    });
  }

  if (cardDrillRangeBhawal && jurisdictionModal) {
    cardDrillRangeBhawal.addEventListener('click', () => {
      jurisdictionModal.style.display = 'none';
      window.AppDrillDown('range', 'Bhawal Range');
    });
  }

  beatPills.forEach(pill => {
    pill.addEventListener('click', () => {
      if (jurisdictionModal) jurisdictionModal.style.display = 'none';
      const beatName = pill.dataset.beat;
      window.AppDrillDown('beat', beatName);
    });
  });

  if (bcDivision) {
    bcDivision.addEventListener('click', () => {
      window.AppDrillDown('division', 'Bhawal National Park');
    });
  }
  if (bcRange) {
    bcRange.addEventListener('click', () => {
      if (currentJurisdiction.range) {
        window.AppDrillDown('range', currentJurisdiction.range);
      }
    });
  }
  if (bcBeat) {
    bcBeat.addEventListener('click', () => {
      if (currentJurisdiction.beat) {
        window.AppDrillDown('beat', currentJurisdiction.beat);
      }
    });
  }

  if (btnResetToDivision) {
    btnResetToDivision.addEventListener('click', () => {
      window.AppDrillDown('division', 'Bhawal National Park');
    });
  }
}

function setupUserAuth() {
  const btnOpenLoginModal = document.getElementById('btnOpenLoginModal');
  const userProfileBadge = document.getElementById('userProfileBadge');
  const userRoleTag = document.getElementById('userRoleTag');
  const userNameText = document.getElementById('userNameText');
  const btnLogoutMini = document.getElementById('btnLogoutMini');
  const userLoginModal = document.getElementById('userLoginModal');
  const btnCloseLoginModal = document.getElementById('btnCloseLoginModal');
  const userLoginForm = document.getElementById('userLoginForm');
  const inputUsername = document.getElementById('inputUsername');
  const inputPassword = document.getElementById('inputPassword');
  const loginAlertBox = document.getElementById('loginAlertBox');
  const navAdminLink = document.getElementById('navAdminLink');
  const quickRoleButtons = document.querySelectorAll('.btn-role-quick');

  const TOKEN_KEY = 'fd_lms_token';

  function renderUserUI(user) {
    if (user && user.username) {
      if (btnOpenLoginModal) btnOpenLoginModal.style.display = 'none';
      if (userProfileBadge) userProfileBadge.style.display = 'inline-flex';
      if (userNameText) userNameText.textContent = user.full_name || user.username;

      let tagText = 'User';
      let tagBg = '#38bdf8';
      if (user.role === 'admin') {
        tagText = 'DFO Admin';
        tagBg = '#10b981';
      } else if (user.role === 'range_officer') {
        tagText = user.assigned_range ? user.assigned_range.replace(' Range', '') : 'RO';
        tagBg = '#f59e0b';
      } else if (user.role === 'beat_officer') {
        tagText = user.assigned_beat ? user.assigned_beat.replace(' Beat', '') : 'BO';
        tagBg = '#06b6d4';
      } else if (user.role === 'guest') {
        tagText = 'Guest';
        tagBg = '#64748b';
      }
      if (userRoleTag) {
        userRoleTag.textContent = tagText;
        userRoleTag.style.background = tagBg;
      }

      if (navAdminLink) {
        navAdminLink.style.display = (user.role === 'admin') ? 'inline-flex' : 'none';
      }

      if (user.role === 'range_officer' && user.assigned_range) {
        window.AppDrillDown('range', user.assigned_range);
      } else if (user.role === 'beat_officer' && user.assigned_beat) {
        window.AppDrillDown('beat', user.assigned_beat);
      }
    } else {
      if (btnOpenLoginModal) btnOpenLoginModal.style.display = 'inline-flex';
      if (userProfileBadge) userProfileBadge.style.display = 'none';
      if (navAdminLink) navAdminLink.style.display = 'none';
    }
  }

  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Unauthorized');
        return res.json();
      })
      .then(data => {
        renderUserUI(data && data.user ? data.user : data);
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        renderUserUI(null);
      });
  } else {
    renderUserUI(null);
  }

  if (btnOpenLoginModal && userLoginModal) {
    btnOpenLoginModal.addEventListener('click', () => {
      userLoginModal.style.display = 'flex';
      if (loginAlertBox) loginAlertBox.style.display = 'none';
    });
  }

  if (btnCloseLoginModal && userLoginModal) {
    btnCloseLoginModal.addEventListener('click', () => {
      userLoginModal.style.display = 'none';
    });
  }

  async function performLogin(username, password) {
    if (loginAlertBox) loginAlertBox.style.display = 'none';
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();
      if (!res.ok) {
        if (loginAlertBox) {
          loginAlertBox.textContent = data.detail || 'Invalid username or password.';
          loginAlertBox.style.display = 'block';
        }
        return false;
      }

      localStorage.setItem(TOKEN_KEY, data.access_token);
      renderUserUI(data.user);
      if (userLoginModal) userLoginModal.style.display = 'none';
      return true;
    } catch (err) {
      if (loginAlertBox) {
        loginAlertBox.textContent = 'Server connection error. Please try again.';
        loginAlertBox.style.display = 'block';
      }
      return false;
    }
  }

  if (userLoginForm) {
    userLoginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const u = inputUsername ? inputUsername.value.trim() : '';
      const p = inputPassword ? inputPassword.value : '';
      if (!u || !p) return;
      performLogin(u, p);
    });
  }

  quickRoleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const u = btn.dataset.u;
      const p = btn.dataset.p;
      if (inputUsername) inputUsername.value = u;
      if (inputPassword) inputPassword.value = p;
      performLogin(u, p);
    });
  });

  if (btnLogoutMini) {
    btnLogoutMini.addEventListener('click', async () => {
      try {
        const curToken = localStorage.getItem(TOKEN_KEY);
        if (curToken) {
          await fetch('/api/auth/logout', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${curToken}` }
          });
        }
      } catch (e) {}
      localStorage.removeItem(TOKEN_KEY);
      renderUserUI(null);
      window.AppDrillDown('division', 'Bhawal National Park');
    });
  }
}


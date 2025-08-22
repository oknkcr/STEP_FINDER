from flask import Flask, request, send_file, jsonify, Response
from flask_cors import CORS
import os
import trimesh
from werkzeug.utils import secure_filename
import json
import difflib

app = Flask(__name__)
CORS(app)  # CORS'u etkinleştir
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CONVERTED_FOLDER'] = 'converted'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# Klasörleri oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CONVERTED_FOLDER'], exist_ok=True)

# STEP Finder için gerekli değişkenler
INDEX_FILE = "index.json"
index_data = {"index": {}, "paths": []}

# Index dosyasını yükle
if os.path.exists(INDEX_FILE):
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
    except:
        index_data = {"index": {}, "paths": []}

@app.route('/')
def index():
    # HTML içeriğini doğrudan döndür
    return Response('''
    <!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>STEP Finder ve GLB Dönüştürücü</title>
  <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    body {
      background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
      color: #fff;
      min-height: 100vh;
      padding: 20px;
    }
    
    .container {
      max-width: 1400px;
      margin: 0 auto;
    }
    
    header {
      text-align: center;
      margin-bottom: 30px;
      padding: 20px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 15px;
      backdrop-filter: blur(10px);
    }
    
    h1 {
      font-size: 2.5rem;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 15px;
    }
    
    h1 i {
      color: #fdbb2d;
    }
    
    .subtitle {
      font-size: 1.2rem;
      opacity: 0.9;
    }
    
    .tab-container {
      margin-bottom: 20px;
    }
    
    .tabs {
      display: flex;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 10px;
      overflow: hidden;
      margin-bottom: 20px;
    }
    
    .tab {
      flex: 1;
      padding: 15px;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: bold;
    }
    
    .tab.active {
      background: rgba(253, 187, 45, 0.3);
    }
    
    .tab:hover {
      background: rgba(255, 255, 255, 0.1);
    }
    
    .tab-content {
      display: none;
    }
    
    .tab-content.active {
      display: block;
    }
    
    .main-content {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
      margin-bottom: 30px;
    }
    
    .panel {
      flex: 1;
      min-width: 300px;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 15px;
      padding: 20px;
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(10px);
    }
    
    .viewer-container {
      flex: 1;
      min-width: 300px;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 15px;
      padding: 15px;
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(10px);
    }
    
    model-viewer {
      width: 100%;
      height: 400px;
      border-radius: 10px;
      overflow: hidden;
      --poster-color: transparent;
    }
    
    .control-group {
      margin-bottom: 20px;
    }
    
    .control-group h3 {
      margin-bottom: 15px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    .control-group h3 i {
      color: #fdbb2d;
    }
    
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
      color: white;
      border: none;
      padding: 12px 20px;
      border-radius: 50px;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.3s ease;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
      margin-right: 10px;
      margin-bottom: 10px;
      text-decoration: none;
    }
    
    .btn:hover {
      transform: translateY(-3px);
      box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
    }
    
    .btn-convert {
      background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
    }
    
    .btn-download {
      background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%);
    }
    
    .btn-finder {
      background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%);
    }
    
    .btn i {
      font-size: 1.2rem;
    }
    
    .file-input {
      display: none;
    }
    
    .file-info {
      margin-top: 15px;
      padding: 10px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 8px;
    }
    
    .progress-container {
      margin-top: 15px;
    }
    
    .progress-bar {
      width: 100%;
      height: 10px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 5px;
      overflow: hidden;
      margin-top: 5px;
    }
    
    .progress {
      height: 100%;
      background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
      width: 0%;
      transition: width 0.3s ease;
    }
    
    .status {
      margin-top: 10px;
      font-size: 0.9rem;
    }
    
    .search-results {
      height: 300px;
      overflow-y: auto;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 10px;
      margin-top: 15px;
    }
    
    .result-item {
      padding: 10px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      cursor: pointer;
      transition: background 0.3s ease;
    }
    
    .result-item:hover {
      background: rgba(255, 255, 255, 0.1);
    }
    
    .result-item:last-child {
      border-bottom: none;
    }
    
    .directories-list {
      margin-top: 15px;
      max-height: 150px;
      overflow-y: auto;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 10px;
    }
    
    .directory-item {
      padding: 5px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .remove-dir {
      color: #ff5e62;
      cursor: pointer;
      font-weight: bold;
    }
    
    .info-panel {
      background: rgba(0, 0, 0, 0.2);
      border-radius: 15px;
      padding: 20px;
      margin-top: 20px;
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(10px);
    }
    
    .info-panel h2 {
      margin-bottom: 15px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    .info-panel h2 i {
      color: #fdbb2d;
    }
    
    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 15px;
    }
    
    .info-item {
      background: rgba(255, 255, 255, 0.1);
      padding: 15px;
      border-radius: 10px;
    }
    
    .info-item h4 {
      margin-bottom: 5px;
      color: #fdbb2d;
    }
    
    footer {
      text-align: center;
      margin-top: 30px;
      padding: 20px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 15px;
      backdrop-filter: blur(10px);
    }
    
    @media (max-width: 768px) {
      .main-content {
        flex-direction: column;
      }
      
      h1 {
        font-size: 2rem;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1><i class="fas fa-search"></i> STEP Finder ve GLB Dönüştürücü</h1>
      <p class="subtitle">STEP dosyalarını bulun, dönüştürün ve görüntüleyin</p>
    </header>
    
    <div class="tab-container">
      <div class="tabs">
        <div class="tab active" data-tab="finder">STEP Finder</div>
        <div class="tab" data-tab="converter">GLB Dönüştürücü</div>
      </div>
      
      <!-- STEP Finder Tab -->
      <div class="tab-content active" id="finder-tab">
        <div class="main-content">
          <div class="panel">
            <div class="control-group">
              <h3><i class="fas fa-search"></i> Parça Numarası Ara</h3>
              <input type="text" id="partSearch" placeholder="Parça numarası veya dosya adı girin..." class="file-input" style="display: block; width: 100%; padding: 10px; border-radius: 5px; border: none; margin-bottom: 10px; background: rgba(255,255,255,0.1); color: white;">
              <button id="searchBtn" class="btn btn-finder">
                <i class="fas fa-search"></i> Ara
              </button>
              
              <div class="control-group">
                <h3><i class="fas fa-folder"></i> Dizin Yönetimi</h3>
                <button id="addDirectoryBtn" class="btn">
                  <i class="fas fa-folder-plus"></i> Dizin Ekle
                </button>
                <button id="indexBtn" class="btn">
                  <i class="fas fa-sync"></i> Yeniden İndeksle
                </button>
                
                <div class="directories-list" id="directoriesList">
                  <div class="directory-item">
                    <span>Henüz dizin eklenmedi</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="panel">
            <div class="control-group">
              <h3><i class="fas fa-list"></i> Bulunan Dosyalar</h3>
              <div class="search-results" id="searchResults">
                <div class="result-item">Arama yapıldıktan sonra sonuçlar burada görünecek</div>
              </div>
              
              <div style="margin-top: 15px;">
                <button id="openFileBtn" class="btn" disabled>
                  <i class="fas fa-folder-open"></i> Dosyayı Aç
                </button>
                <button id="convertFoundBtn" class="btn btn-convert" disabled>
                  <i class="fas fa-exchange-alt"></i> Dönüştür
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- GLB Converter Tab -->
      <div class="tab-content" id="converter-tab">
        <div class="main-content">
          <div class="panel">
            <div class="control-group">
              <h3><i class="fas fa-file-import"></i> STEP Dosyası Seçin</h3>
              <label for="stepFileInput" class="btn">
                <i class="fas fa-upload"></i> STEP Dosyası Seç
              </label>
              <input type="file" id="stepFileInput" class="file-input" accept=".step,.stp" />
              <div class="file-info">
                <p id="stepFileName">Henüz bir dosya seçilmedi</p>
                <p id="stepFileSize">-</p>
              </div>
            </div>
            
            <div class="control-group">
              <h3><i class="fas fa-cogs"></i> Dönüştürme Ayarları</h3>
              <div class="progress-container">
                <label>Dönüştürme Durumu:</label>
                <div class="progress-bar">
                  <div class="progress" id="conversionProgress"></div>
                </div>
                <div class="status" id="conversionStatus">Hazır</div>
              </div>
            </div>
            
            <div class="control-group">
              <button id="convertBtn" class="btn btn-convert" disabled>
                <i class="fas fa-exchange-alt"></i> Dönüştür
              </button>
              <a id="downloadBtn" class="btn btn-download" style="display: none;">
                <i class="fas fa-download"></i> GLB'yi İndir
              </a>
            </div>
          </div>
          
          <div class="viewer-container">
            <div class="control-group">
              <h3><i class="fas fa-eye"></i> 3B Model Görüntüleyici</h3>
              <model-viewer id="viewer"
                alt="3B Model"
                shadow-intensity="1"
                camera-controls
                auto-rotate
                ar
                environment-image="neutral"
                exposure="1.0">
              </model-viewer>
              <p id="viewerStatus" style="text-align: center; margin-top: 10px;">Dönüştürülen model burada görüntülenecek</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="info-panel">
      <h2><i class="fas fa-info-circle"></i> Nasıl Kullanılır?</h2>
      <div class="info-grid">
        <div class="info-item">
          <h4>STEP Finder</h4>
          <p>1. Dizin ekleyin ve indeksleyin</p>
          <p>2. Parça numarası veya dosya adı ile arama yapın</p>
          <p>3. Bulunan dosyayı açın veya dönüştürün</p>
        </div>
        <div class="info-item">
          <h4>GLB Dönüştürücü</h4>
          <p>1. STEP dosyası seçin</p>
          <p>2. Dönüştür butonuna tıklayın</p>
          <p>3. Görüntüleyin ve indirin</p>
        </div>
        <div class="info-item">
          <h4>Özellikler</h4>
          <p>• STEP/STP dosya arama</p>
          <p>• GLB formatına dönüştürme</p>
          <p>• 3B model görüntüleme</p>
        </div>
      </div>
    </div>
    
    <footer>
      <p>© 2025 STEP Finder ve GLB Dönüştürücü | OKAN KOÇER</p>
    </footer>
  </div>

  <script>
    // Elementleri seçme
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    const stepFileInput = document.getElementById('stepFileInput');
    const stepFileName = document.getElementById('stepFileName');
    const stepFileSize = document.getElementById('stepFileSize');
    const convertBtn = document.getElementById('convertBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const conversionProgress = document.getElementById('conversionProgress');
    const conversionStatus = document.getElementById('conversionStatus');
    const viewer = document.getElementById('viewer');
    const viewerStatus = document.getElementById('viewerStatus');
    const partSearch = document.getElementById('partSearch');
    const searchBtn = document.getElementById('searchBtn');
    const searchResults = document.getElementById('searchResults');
    const openFileBtn = document.getElementById('openFileBtn');
    const convertFoundBtn = document.getElementById('convertFoundBtn');
    const addDirectoryBtn = document.getElementById('addDirectoryBtn');
    const indexBtn = document.getElementById('indexBtn');
    const directoriesList = document.getElementById('directoriesList');
    
    let selectedFile = null;
    let foundFiles = [];
    let selectedFoundFile = null;
    
    // Sayfa yüklendiğinde dizinleri getir
    window.addEventListener('load', () => {
      fetch('/get_directories')
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            updateDirectoriesList(data.directories);
          }
        });
    });
    
    // Sekme değiştirme
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const tabId = tab.getAttribute('data-tab');
        
        tabs.forEach(t => t.classList.remove('active'));
        tabContents.forEach(tc => tc.classList.remove('active'));
        
        tab.classList.add('active');
        document.getElementById(`${tabId}-tab`).classList.add('active');
      });
    });
    
    // Dosya seçme işlemi
    stepFileInput.addEventListener('change', (event) => {
      const file = event.target.files[0];
      if (file) {
        selectedFile = file;
        stepFileName.textContent = file.name;
        stepFileSize.textContent = formatFileSize(file.size);
        convertBtn.disabled = false;
        conversionStatus.textContent = "Dönüştürmeye hazır";
        
        // Önceki dönüştürmeyi temizle
        downloadBtn.style.display = "none";
        viewer.src = "";
        viewerStatus.textContent = "Dönüştürülen model burada görüntülenecek";
      }
    });
    
    // Dönüştürme butonu
    convertBtn.addEventListener('click', async () => {
      if (!selectedFile) return;
      
      // FormData oluştur ve dosyayı sunucuya gönder
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      try {
        convertBtn.disabled = true;
        conversionStatus.textContent = "Dosya yükleniyor...";
        conversionProgress.style.width = "30%";
        
        // Dosyayı sunucuya yükle
        const uploadResponse = await fetch('/upload', {
          method: 'POST',
          body: formData
        });
        
        const uploadResult = await uploadResponse.json();
        
        if (!uploadResult.success) {
          throw new Error(uploadResult.error || "Dosya yüklenirken hata oluştu");
        }
        
        conversionStatus.textContent = "Dosya dönüştürülüyor...";
        conversionProgress.style.width = "60%";
        
        // Dönüştürme işlemini başlat
        const convertResponse = await fetch('/convert', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ filename: uploadResult.filename })
        });
        
        const convertResult = await convertResponse.json();
        
        if (!convertResult.success) {
          throw new Error(convertResult.error || "Dönüştürme sırasında hata oluştu");
        }
        
        conversionStatus.textContent = "Dönüştürme tamamlandı!";
        conversionProgress.style.width = "100%";
        
        // Görüntüleyiciyi güncelle
        viewer.src = `/view/${convertResult.converted_filename}`;
        viewerStatus.textContent = "Model başarıyla yüklendi";
        
        // İndirme butonunu güncelle ve göster
        downloadBtn.href = convertResult.download_url;
        downloadBtn.style.display = "inline-flex";
        
      } catch (error) {
        console.error("Hata:", error);
        conversionStatus.textContent = "Hata: " + error.message;
        convertBtn.disabled = false;
      }
    });
    
    // Arama butonu
    searchBtn.addEventListener('click', () => {
      const query = partSearch.value.trim();
      if (!query) return;
      
      // Sunucuda arama yap
      fetch('/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: query })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          foundFiles = data.results;
          displaySearchResults(foundFiles);
        } else {
          searchResults.innerHTML = `<div class="result-item">Arama hatası: ${data.error}</div>`;
        }
      })
      .catch(error => {
        searchResults.innerHTML = `<div class="result-item">Arama sırasında hata oluştu: ${error.message}</div>`;
      });
    });
    
    // Arama sonuçlarını göster
    function displaySearchResults(results) {
      searchResults.innerHTML = '';
      
      if (results.length === 0) {
        searchResults.innerHTML = '<div class="result-item">Hiç dosya bulunamadı</div>';
        openFileBtn.disabled = true;
        convertFoundBtn.disabled = true;
        return;
      }
      
      results.forEach((result, index) => {
        const item = document.createElement('div');
        item.className = 'result-item';
        item.innerHTML = `
          <strong>${result.name}</strong><br>
          <small>${result.path}</small><br>
          <small>Eşleşme: ${result.score}%</small>
        `;
        
        item.addEventListener('click', () => {
          document.querySelectorAll('.result-item').forEach(i => i.style.background = '');
          item.style.background = 'rgba(253, 187, 45, 0.2)';
          selectedFoundFile = result;
          openFileBtn.disabled = false;
          convertFoundBtn.disabled = false;
        });
        
        searchResults.appendChild(item);
      });
    }
    
    // Bulunan dosyayı aç
    openFileBtn.addEventListener('click', () => {
      if (!selectedFoundFile) return;
      
      // Sunucuya dosyayı açma isteği gönder
      fetch('/open_file', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ path: selectedFoundFile.path })
      })
      .then(response => response.json())
      .then(data => {
        if (!data.success) {
          alert('Dosya açılamadı: ' + data.error);
        }
      })
      .catch(error => {
        alert('Dosya açılamadı: ' + error.message);
      });
    });
    
    // Bulunan dosyayı dönüştür
    convertFoundBtn.addEventListener('click', () => {
      if (!selectedFoundFile) return;
      
      // Dönüştürme sekmesine geç ve dosyayı yükle
      tabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(tc => tc.classList.remove('active'));
      
      document.querySelector('[data-tab="converter"]').classList.add('active');
      document.getElementById('converter-tab').classList.add('active');
      
      // Dosya bilgilerini göster (simülasyon)
      stepFileName.textContent = selectedFoundFile.name;
      stepFileSize.textContent = "Boyut bilinmiyor";
      convertBtn.disabled = false;
      conversionStatus.textContent = "Dönüştürmeye hazır";
      
      // Sunucuya dönüştürme isteği gönder
      fetch('/convert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ filepath: selectedFoundFile.path })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          conversionStatus.textContent = "Dönüştürme tamamlandı!";
          conversionProgress.style.width = "100%";
          
          // Görüntüleyiciyi güncelle
          viewer.src = `/view/${data.converted_filename}`;
          viewerStatus.textContent = "Model başarıyla yüklendi";
          
          // İndirme butonunu güncelle ve göster
          downloadBtn.href = data.download_url;
          downloadBtn.style.display = "inline-flex";
        } else {
          conversionStatus.textContent = "Hata: " + data.error;
        }
      })
      .catch(error => {
        conversionStatus.textContent = "Hata: " + error.message;
      });
    });
    
    // Dizin ekleme
    addDirectoryBtn.addEventListener('click', () => {
      // Kullanıcıdan dizin yolu al
      const directory = prompt('Lütfen dizin yolunu girin:');
      if (!directory) return;
      
      fetch('/add_directory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ directory: directory })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert(data.message);
          // Dizin listesini güncelle
          updateDirectoriesList(data.directories);
        } else {
          alert('Dizin eklenemedi: ' + data.error);
        }
      })
      .catch(error => {
        alert('Dizin eklenemedi: ' + error.message);
      });
    });
    
    // Dizin listesini güncelle
    function updateDirectoriesList(directories) {
      directoriesList.innerHTML = '';
      
      if (!directories || directories.length === 0) {
        directoriesList.innerHTML = '<div class="directory-item"><span>Henüz dizin eklenmedi</span></div>';
        return;
      }
      
      directories.forEach((dir, index) => {
        const item = document.createElement('div');
        item.className = 'directory-item';
        item.innerHTML = `
          <span title="${dir}">${dir.length > 40 ? dir.substring(0, 40) + '...' : dir}</span>
          <span class="remove-dir" data-index="${index}">×</span>
        `;
        directoriesList.appendChild(item);
      });
      
      // Dizin kaldırma işlevselliği ekle
      document.querySelectorAll('.remove-dir').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const index = e.target.getAttribute('data-index');
          removeDirectory(index);
        });
      });
    }
    
    // Dizin kaldırma
    function removeDirectory(index) {
      fetch('/remove_directory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ index: parseInt(index) })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Dizin listesini güncelle
          updateDirectoriesList(data.directories);
        } else {
          alert('Dizin kaldırılamadı: ' + data.error);
        }
      })
      .catch(error => {
        alert('Dizin kaldırılamadı: ' + error.message);
      });
    }
    
    // Yeniden indeksleme
    indexBtn.addEventListener('click', () => {
      fetch('/reindex', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert(data.message);
        } else {
          alert('İndeksleme hatası: ' + data.error);
        }
      })
      .catch(error => {
        alert('İndeksleme hatası: ' + error.message);
      });
    });
    
    // Dosya boyutunu formatlama
    function formatFileSize(bytes) {
      if (bytes < 1024) return bytes + ' bytes';
      else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
      else return (bytes / 1048576).toFixed(2) + ' MB';
    }
  </script>
</body>
</html>
    ''', mimetype='text/html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Dosya seçilmedi'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filesize': os.path.getsize(filepath)
        })
    
    return jsonify({'error': 'Geçersiz dosya formatı'})

@app.route('/convert', methods=['POST'])
def convert_file():
    data = request.json
    
    # Dosya yolu veya dosya adı ile çalışma
    if 'filepath' in data:
        input_path = data['filepath']
        output_filename = os.path.splitext(os.path.basename(input_path))[0] + '.glb'
    elif 'filename' in data:
        input_filename = data['filename']
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        output_filename = os.path.splitext(input_filename)[0] + '.glb'
    else:
        return jsonify({'error': 'Dosya bilgisi eksik'})
    
    output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)
    
    try:
        # STEP dosyasını yükle ve GLB'ye dönüştür
        mesh = trimesh.load(input_path)
        mesh.export(output_path, file_type='glb')
        
        return jsonify({
            'success': True,
            'converted_filename': output_filename,
            'download_url': f'/download/{output_filename}'
        })
    except Exception as e:
        return jsonify({'error': f'Dönüştürme hatası: {str(e)}'})

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(
        os.path.join(app.config['CONVERTED_FOLDER'], filename),
        as_attachment=True
    )

@app.route('/view/<filename>')
def view_file(filename):
    return send_file(
        os.path.join(app.config['CONVERTED_FOLDER'], filename)
    )

@app.route('/search', methods=['POST'])
def search_files():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'Arama sorgusu eksik'})
    
    query = data['query'].lower()
    results = []
    
    for name, path in index_data['index'].items():
        ratio = difflib.SequenceMatcher(None, query, name.lower()).ratio()
        score = int(ratio * 100)
        
        if query in name.lower() or score > 40:
            results.append({
                'name': name,
                'path': path,
                'score': score
            })
    
    # Skora göre sırala
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        'success': True,
        'results': results
    })

@app.route('/open_file', methods=['POST'])
def open_file():
    data = request.json
    if not data or 'path' not in data:
        return jsonify({'error': 'Dosya yolu eksik'})
    
    try:
        path = data['path']
        if os.name == 'nt':
            os.startfile(path)
        else:
            import subprocess
            subprocess.call(['open', path])
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/add_directory', methods=['POST'])
def add_directory():
    data = request.json
    if not data or 'directory' not in data:
        return jsonify({'error': 'Dizin bilgisi eksik'})
    
    try:
        directory = data['directory']
        if os.path.isdir(directory):
            if directory not in index_data['paths']:
                index_data['paths'].append(directory)
                
                # Index dosyasını kaydet
                with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, indent=2)
                
                return jsonify({
                    'success': True,
                    'message': f'Dizin eklendi: {directory}',
                    'directories': index_data['paths']
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Bu dizin zaten eklenmiş'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Geçerli bir dizin değil'
            })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_directories', methods=['GET'])
def get_directories():
    return jsonify({
        'success': True,
        'directories': index_data['paths']
    })

@app.route('/remove_directory', methods=['POST'])
def remove_directory():
    data = request.json
    if not data or 'index' not in data:
        return jsonify({'error': 'Dizin indeksi eksik'})
    
    try:
        index = data['index']
        if 0 <= index < len(index_data['paths']):
            removed_dir = index_data['paths'].pop(index)
            
            # Index dosyasını kaydet
            with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)
            
            return jsonify({
                'success': True,
                'message': f'Dizin kaldırıldı: {removed_dir}',
                'directories': index_data['paths']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Geçersiz dizin indeksi'
            })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/reindex', methods=['POST'])
def reindex():
    try:
        index_data['index'] = {}
        
        for path in index_data['paths']:
            if os.path.exists(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(('.step', '.stp')):
                            filepath = os.path.join(root, file)
                            index_data['index'][file] = filepath
        
        # Index dosyasını kaydet
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'{len(index_data["index"])} dosya indekslendi'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['step', 'stp']

if __name__ == '__main__':
    app.run(debug=True)
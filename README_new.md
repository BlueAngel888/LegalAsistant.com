# OCR Flask Application

Un proiect Flask complet pentru procesarea OCR cu flux de plată urmată de upload și procesare asincronă.

## Structură Proiect

```
├── main_new.py              # Server Flask principal
├── templates/
│   ├── index_new.html       # Pagina de plată
│   └── upload_new.html      # Pagina de upload și rezultate
├── static/
│   └── script_new.js        # JavaScript pentru upload și OCR
├── requirements_new.txt     # Dependințe Python
└── README_new.md           # Această documentație
```

## Fluxul Aplicației

1. **Pagina Principală** (`/`) - Buton de plată simulată
2. **Procesare Plată** (`/create-payment`) - Simulează plata și redirecționează
3. **Pagina Upload** (`/upload`) - Accesibilă doar după plată
4. **API OCR** (`/api/ocr`) - Procesează imaginile asincron

## Instalare și Rulare

### În Replit:

1. **Copiază fișierele** în proiectul tău Replit
2. **Instalează dependințele**:
   ```bash
   pip install -r requirements_new.txt
   ```

3. **Pentru OCR real cu Tesseract**:
   ```bash
   # Instalează Tesseract în Replit
   sudo apt-get update
   sudo apt-get install tesseract-ocr
   sudo apt-get install tesseract-ocr-ron  # Pentru română
   ```

4. **Rulează aplicația**:
   ```bash
   python main_new.py
   ```

### Configurare OCR Real

Pentru a activa OCR-ul real cu Tesseract, modifică funcția `perform_ocr` în `main_new.py`:

```python
def perform_ocr(image):
    import pytesseract
    
    # Optimizează imaginea pentru OCR
    image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
    
    # Configurează OCR
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, lang='eng', config=config)
    
    return text.strip()
```

## Caracteristici

### Frontend
- Design modern și responsive
- Drag & drop pentru imagini
- Animații și feedback vizual
- Gestionarea erorilor

### Backend
- Simulare plată (ușor de integra cu Stripe real)
- Verificare autentificare după plată
- API RESTful pentru OCR
- Gestionarea erorilor și validări

### OCR
- Suport pentru toate formatele de imagine
- Optimizare automată pentru OCR
- Simulare realistă când Tesseract nu e disponibil
- Marcaj clar pentru activarea OCR-ului real

## API Endpoints

- `GET /` - Pagina principală cu plata
- `POST /create-payment` - Procesează plata (simulată)
- `GET /upload` - Pagina de upload (necesită plată)
- `POST /api/ocr` - Procesează imaginea cu OCR
- `GET /health` - Status aplicație

## Utilizare

1. Accesează pagina principală
2. Apasă butonul de plată
3. Încarcă o imagine pe pagina de upload
4. Vezi textul extras automat afișat

## Note Tehnice

- Fluxul de plată este separat de OCR (non-blocking)
- Sesiunile Flask gestionează starea utilizatorului
- OCR-ul se face asincron prin AJAX
- Validări complete pentru fișiere și securitate
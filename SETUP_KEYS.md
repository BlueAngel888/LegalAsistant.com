# Configurarea Cheilor API pentru Legal Assistant

## Unde să introduci cheile API

### În Replit:
1. **Deschide panoul Secrets în Replit**
   - Click pe "Secrets" în sidebar-ul din stânga
   - Sau accesează Tools > Secrets

2. **Adaugă următoarele secrets:**

#### Pentru OpenAI:
- **Key:** `OPENAI_API_KEY`
- **Value:** Cheia ta OpenAI (începe cu `sk-`)

#### Pentru Stripe:
- **Key:** `STRIPE_SECRET_KEY`  
- **Value:** Cheia secretă Stripe (începe cu `sk_test_` sau `sk_live_`)

- **Key:** `STRIPE_PUBLIC_KEY`
- **Value:** Cheia publică Stripe (începe cu `pk_test_` sau `pk_live_`)

### Cum să obții cheile:

#### OpenAI API Key:
1. Mergi la https://platform.openai.com
2. Creează cont sau loghează-te
3. Mergi la "API Keys" în meniul din stânga
4. Click "Create new secret key"
5. Copiază cheia (începe cu `sk-`)

#### Stripe Keys:
1. Mergi la https://stripe.com
2. Creează cont sau loghează-te  
3. Mergi la Dashboard > Developers > API keys
4. Copiază "Publishable key" și "Secret key"

## Important:
- **Nu pune cheile în codul sursă!**
- Folosește doar panoul Secrets din Replit
- Pentru testare, folosește cheile de test (`sk_test_` și `pk_test_`)
- Pentru producție, folosește cheile live (`sk_live_` și `pk_live_`)

## După adăugarea cheilor:
1. Aplicația va reporni automat
2. Testează funcționalitatea de upload și analiză
3. Verifică că plățile funcționează corect în modul test
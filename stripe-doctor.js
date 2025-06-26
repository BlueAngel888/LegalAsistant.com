#!/usr/bin/env node

const Stripe = require('stripe');
const axios = require('axios');

// ANSI Colors
const colors = {
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    reset: '\x1b[0m',
    bold: '\x1b[1m'
};

const log = (message, color = '') => console.log(`${color}${message}${colors.reset}`);
const success = (message) => log(`✅ ${message}`, colors.green);
const error = (message) => log(`❌ ${message}`, colors.red);
const warning = (message) => log(`⚠️  ${message}`, colors.yellow);
const info = (message) => log(`ℹ️  ${message}`, colors.blue);

let issues = [];
let stripe = null;

async function main() {
    log(`${colors.bold}🔍 Stripe Checkout Diagnostic Tool${colors.reset}`);
    log('='.repeat(50));

    await step1_verifyStripeKeys();
    await step2_verifyCheckoutEndpoint();
    await step3_validateSession();
    await step4_verifyDomainHTTPS();
    await step5_verifyRegisteredDomains();
    await step6_finalReport();
}

// 1️⃣ Verificarea cheilor Stripe
async function step1_verifyStripeKeys() {
    log(`${colors.bold}1️⃣ Verificarea cheilor Stripe${colors.reset}`);
    
    const secretKey = process.env.STRIPE_SECRET_KEY;
    const publishableKey = process.env.STRIPE_PUBLISHABLE_KEY;
    
    if (!secretKey) {
        error('STRIPE_SECRET_KEY lipsește din environment');
        issues.push('❌ STRIPE_SECRET_KEY nu este setat');
        return;
    }
    
    if (!publishableKey) {
        warning('STRIPE_PUBLISHABLE_KEY lipsește (opțional pentru backend)');
    }
    
    // Verifică dacă cheile sunt mixed (test/live)
    const secretIsTest = secretKey.startsWith('sk_test_');
    const secretIsLive = secretKey.startsWith('sk_live_');
    const pubIsTest = publishableKey?.startsWith('pk_test_');
    const pubIsLive = publishableKey?.startsWith('pk_live_');
    
    if (publishableKey && ((secretIsTest && pubIsLive) || (secretIsLive && pubIsTest))) {
        error('Cheile Stripe sunt mixed: una test, una live!');
        issues.push('❌ Chei Stripe mixed (test/live)');
        return;
    }
    
    if (secretIsTest) {
        info('Folosești chei Stripe TEST (OK pentru development)');
    } else if (secretIsLive) {
        warning('Folosești chei Stripe LIVE (verifică dacă intenționezi acest lucru)');
    }
    
    // Testează conectivitatea
    try {
        stripe = new Stripe(secretKey);
        const account = await stripe.accounts.retrieve();
        success(`Chei Stripe valide - Account ID: ${account.id}`);
    } catch (err) {
        error(`Eroare la conectarea cu Stripe: ${err.message}`);
        issues.push(`❌ Conectare Stripe eșuată: ${err.message}`);
    }
}

// 2️⃣ Verificarea endpoint-ului checkout
async function step2_verifyCheckoutEndpoint() {
    log(`${colors.bold}2️⃣ Verificarea endpoint-ului /create-checkout-session${colors.reset}`);
    
    const baseUrl = 'http://127.0.0.1:5000'; // Flask default port
    const endpoint = `${baseUrl}/create-checkout-session`;
    
    try {
        // Creează date de test pentru form
        const formData = new URLSearchParams({
            'document_country': 'RO',
            'analysis_language': 'ro',
            'files': '' // Simulated file upload
        });
        
        const response = await axios.post(endpoint, formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            maxRedirects: 0, // Nu urma redirecturile automat
            validateStatus: (status) => status < 500 // Accept 3xx codes
        });
        
        if (response.status === 303) {
            success('Endpoint returnează redirect 303 (corect!)');
            const location = response.headers.location;
            if (location && location.includes('checkout.stripe.com')) {
                success(`Redirect către Stripe detectat: ${location.substring(0, 50)}...`);
                global.stripeCheckoutUrl = location;
            } else {
                error(`Redirect incorect: ${location}`);
                issues.push('❌ Redirect nu duce către Stripe');
            }
        } else if (response.status === 200) {
            if (response.data.redirect_url) {
                success('Endpoint returnează JSON cu redirect_url');
                global.stripeCheckoutUrl = response.data.redirect_url;
            } else {
                warning('Răspuns 200 dar fără redirect_url în JSON');
            }
        } else {
            error(`Status neașteptat: ${response.status}`);
            issues.push(`❌ Status HTTP: ${response.status}`);
        }
        
    } catch (err) {
        if (err.response) {
            error(`Endpoint eșuat: ${err.response.status} - ${err.response.statusText}`);
            if (err.response.data) {
                log(`Body: ${JSON.stringify(err.response.data).substring(0, 200)}...`);
            }
            issues.push(`❌ Endpoint /create-checkout-session: ${err.response.status}`);
        } else {
            error(`Nu pot accesa endpoint-ul: ${err.message}`);
            issues.push(`❌ Server Flask nu răspunde pe port 5000`);
        }
    }
}

// 3️⃣ Validarea sesiunii Stripe
async function step3_validateSession() {
    log(`${colors.bold}3️⃣ Validarea sesiunii Stripe${colors.reset}`);
    
    if (!stripe) {
        warning('Salt peste validare - Stripe nu este inițializat');
        return;
    }
    
    if (!global.stripeCheckoutUrl) {
        warning('Salt peste validare - nu am URL de checkout');
        return;
    }
    
    try {
        // Extrage session ID din URL
        const urlMatch = global.stripeCheckoutUrl.match(/cs_test_[a-zA-Z0-9]+/);
        if (!urlMatch) {
            error('Nu pot extrage session ID din URL-ul Stripe');
            issues.push('❌ URL Stripe malformat');
            return;
        }
        
        const sessionId = urlMatch[0];
        info(`Session ID detectat: ${sessionId}`);
        
        const session = await stripe.checkout.sessions.retrieve(sessionId);
        
        if (session.status === 'open') {
            success('Sesiunea Stripe este OPEN și validă');
        } else {
            warning(`Status sesiune: ${session.status} (ar trebui să fie 'open')`);
        }
        
        if (session.url) {
            success('URL de checkout este prezent în sesiune');
        } else {
            error('URL de checkout lipsește din sesiune');
            issues.push('❌ Sesiune fără URL de checkout');
        }
        
    } catch (err) {
        error(`Eroare la validarea sesiunii: ${err.message}`);
        issues.push(`❌ Validare sesiune: ${err.message}`);
    }
}

// 4️⃣ Verificarea domeniului și HTTPS
async function step4_verifyDomainHTTPS() {
    log(`${colors.bold}4️⃣ Verificarea domeniului și HTTPS${colors.reset}`);
    
    let domain = process.env.SERVER_DOMAIN || 
                 process.env.REPLIT_DEV_DOMAIN ||
                 `${process.env.REPL_SLUG}.${process.env.REPL_OWNER}.repl.co`;
    
    if (!domain) {
        warning('Nu pot determina domeniul serverului');
        domain = 'localhost:5000';
    }
    
    info(`Domeniu detectat: ${domain}`);
    
    if (!domain.startsWith('https://') && !domain.includes('localhost')) {
        error('Domeniul nu folosește HTTPS - Stripe blochează HTTP!');
        issues.push('❌ Domeniu HTTP (Stripe necesită HTTPS)');
    } else if (domain.includes('localhost')) {
        warning('Localhost detectat - OK pentru development, dar Stripe checkout poate să nu funcționeze');
    } else {
        success('Domeniu HTTPS validat');
    }
}

// 5️⃣ Verificarea domeniilor înregistrate în Stripe
async function step5_verifyRegisteredDomains() {
    log(`${colors.bold}5️⃣ Verificarea domeniilor înregistrate în Stripe${colors.reset}`);
    
    if (!stripe) {
        warning('Salt peste verificare - Stripe nu este inițializat');
        return;
    }
    
    try {
        const sessions = await stripe.checkout.sessions.list({ limit: 1 });
        
        if (sessions.data.length > 0) {
            const sampleUrl = sessions.data[0].success_url || sessions.data[0].cancel_url;
            if (sampleUrl) {
                const registeredDomain = new URL(sampleUrl).origin;
                info(`Domeniu înregistrat în Stripe: ${registeredDomain}`);
                
                const currentDomain = process.env.REPLIT_DEV_DOMAIN || 'localhost:5000';
                if (sampleUrl.includes(currentDomain)) {
                    success('Domeniul curent este înregistrat în Stripe');
                } else {
                    warning(`Posibilă nepotrivire de domeniu: ${registeredDomain} vs ${currentDomain}`);
                }
            }
        } else {
            info('Nu există sesiuni anterioare pentru comparația domeniului');
        }
        
    } catch (err) {
        warning(`Nu pot verifica domeniile înregistrate: ${err.message}`);
        log('💡 Verifică manual în Stripe Dashboard → Settings → Branding');
    }
}

// 6️⃣ Raport final
async function step6_finalReport() {
    log(`${colors.bold}6️⃣ Raport Final${colors.reset}`);
    log('='.repeat(50));
    
    if (issues.length === 0) {
        success('🎉 Toate verificările au trecut! Stripe ar trebui să funcționeze.');
        log('\n💡 Dacă pagina tot nu se încarcă, verifică:');
        log('   • Browser cache/cookies');
        log('   • Adblockers care blochează Stripe');
        log('   • Network restrictions');
    } else {
        error(`🚨 ${issues.length} probleme detectate:`);
        log('');
        issues.forEach(issue => log(`   ${issue}`));
        
        log(`\n${colors.bold}🔧 Acțiuni recomandate:${colors.reset}`);
        log('   1. Corectează problemele de mai sus');
        log('   2. Verifică Stripe Dashboard pentru configurări');
        log('   3. Testează din nou cu un browser fresh');
        log('   4. Verifică console-ul browser pentru erori JavaScript');
    }
    
    log('\n📊 Rezumat verificări:');
    log('┌─────────────────────────────────────┬──────────┐');
    log('│ Verificare                          │ Status   │');
    log('├─────────────────────────────────────┼──────────┤');
    log(`│ Chei Stripe                         │ ${stripe ? '✅ OK    ' : '❌ FAIL  '}│`);
    log(`│ Endpoint checkout                   │ ${global.stripeCheckoutUrl ? '✅ OK    ' : '❌ FAIL  '}│`);
    log(`│ Sesiune validă                      │ ${stripe && global.stripeCheckoutUrl ? '✅ OK    ' : '❌ SKIP  '}│`);
    log(`│ HTTPS configurare                   │ ${issues.some(i => i.includes('HTTP')) ? '❌ FAIL  ' : '✅ OK    '}│`);
    log('└─────────────────────────────────────┴──────────┘');
}

// Pornește diagnosticul
main().catch(err => {
    error(`Eroare fatală: ${err.message}`);
    console.error(err);
    process.exit(1);
});
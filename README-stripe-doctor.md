# Stripe Checkout Diagnostic Tool

Diagnostic script pentru identificarea problemelor cu Stripe Checkout în Replit.

## Instalare și rulare

```bash
npm install stripe axios
node stripe-doctor.js
```

## Ce verifică

- ✅ Chei Stripe (validitate, test/live mismatch)
- ✅ Endpoint `/create-checkout-session` (răspuns și redirect)  
- ✅ Validitatea sesiunii Stripe create
- ✅ Configurarea HTTPS (Stripe blochează HTTP)
- ✅ Domeniile înregistrate în Stripe Dashboard

Script-ul va identifica exact ce blochează redirectul către Stripe Checkout și va oferi soluții concrete.
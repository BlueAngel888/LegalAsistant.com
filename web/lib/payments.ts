import Stripe from 'stripe';
import { ANALYSIS_CURRENCY, ANALYSIS_PRICE_CENTS } from './pricing';
import { supabaseAdmin } from './supabase';

export { ANALYSIS_CURRENCY, ANALYSIS_PRICE_CENTS };

export enum PaymentStatus {
  PENDING = 'pending',
  PAID = 'paid',
  USED = 'used',
}

export interface Payment {
  id: string;
  userId: string;
  documentId: string;
  stripeSessionId: string;
  status: PaymentStatus;
  amountCents: number;
  currency: string;
}

let stripeClient: Stripe | null = null;

export function getStripe(): Stripe {
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) {
    throw new Error('STRIPE_SECRET_KEY not configured');
  }
  stripeClient ??= new Stripe(key);
  return stripeClient;
}

export async function createPayment(
  userId: string,
  documentId: string,
  stripeSessionId: string,
): Promise<void> {
  const { error } = await supabaseAdmin.from('payments').insert({
    user_id: userId,
    document_id: documentId,
    stripe_session_id: stripeSessionId,
    amount_cents: ANALYSIS_PRICE_CENTS,
    currency: ANALYSIS_CURRENCY,
    status: PaymentStatus.PENDING,
  });

  if (error) {
    throw new Error(`Failed to create payment: ${error.message}`);
  }
}

/**
 * Marks the payment behind a completed Checkout Session as paid.
 * Only sessions Stripe reports as paid, for the full analysis price, count.
 */
export async function markSessionPaid(session: Stripe.Checkout.Session): Promise<boolean> {
  if (
    session.payment_status !== 'paid' ||
    session.amount_total !== ANALYSIS_PRICE_CENTS ||
    session.currency !== ANALYSIS_CURRENCY
  ) {
    return false;
  }

  const paymentIntent =
    typeof session.payment_intent === 'string' ? session.payment_intent : session.payment_intent?.id;

  const { error } = await supabaseAdmin
    .from('payments')
    .update({
      status: PaymentStatus.PAID,
      stripe_payment_intent_id: paymentIntent ?? null,
      paid_at: new Date().toISOString(),
    })
    .eq('stripe_session_id', session.id)
    .eq('status', PaymentStatus.PENDING);

  if (error) {
    throw new Error(`Failed to mark payment as paid: ${error.message}`);
  }
  return true;
}

/**
 * Returns a paid, not yet used payment for this document. When the webhook has not
 * arrived yet, asks Stripe directly about the session the user just returned from.
 */
export async function findPaidPayment(
  userId: string,
  documentId: string,
  stripeSessionId?: string,
): Promise<Payment | null> {
  const paid = await selectPayment(userId, documentId, PaymentStatus.PAID);
  if (paid || !stripeSessionId) {
    return paid;
  }

  const pending = await selectPayment(userId, documentId, PaymentStatus.PENDING, stripeSessionId);
  if (!pending) {
    return null;
  }

  const session = await getStripe().checkout.sessions.retrieve(stripeSessionId);
  if (!(await markSessionPaid(session))) {
    return null;
  }
  return selectPayment(userId, documentId, PaymentStatus.PAID, stripeSessionId);
}

/** Atomically uses up a paid payment, so one payment buys exactly one analysis. */
export async function claimPayment(paymentId: string): Promise<boolean> {
  const { data, error } = await supabaseAdmin
    .from('payments')
    .update({ status: PaymentStatus.USED, used_at: new Date().toISOString() })
    .eq('id', paymentId)
    .eq('status', PaymentStatus.PAID)
    .select('id');

  if (error) {
    throw new Error(`Failed to claim payment: ${error.message}`);
  }
  return (data ?? []).length === 1;
}

/** Gives the payment back when the analysis failed, so the user can retry without paying again. */
export async function releasePayment(paymentId: string): Promise<void> {
  const { error } = await supabaseAdmin
    .from('payments')
    .update({ status: PaymentStatus.PAID, used_at: null })
    .eq('id', paymentId)
    .eq('status', PaymentStatus.USED);

  if (error) {
    console.error('Failed to release payment:', error);
  }
}

export async function linkPaymentToAnalysis(paymentId: string, analysisId: string): Promise<void> {
  const { error } = await supabaseAdmin
    .from('payments')
    .update({ analysis_id: analysisId })
    .eq('id', paymentId);

  if (error) {
    console.error('Failed to link payment to analysis:', error);
  }
}

async function selectPayment(
  userId: string,
  documentId: string,
  status: PaymentStatus,
  stripeSessionId?: string,
): Promise<Payment | null> {
  let query = supabaseAdmin
    .from('payments')
    .select('*')
    .eq('user_id', userId)
    .eq('document_id', documentId)
    .eq('status', status);

  if (stripeSessionId) {
    query = query.eq('stripe_session_id', stripeSessionId);
  }

  const { data, error } = await query.order('created_at', { ascending: true }).limit(1);

  if (error || !data || data.length === 0) {
    return null;
  }

  const row = data[0];
  return {
    id: row.id,
    userId: row.user_id,
    documentId: row.document_id,
    stripeSessionId: row.stripe_session_id,
    status: row.status,
    amountCents: row.amount_cents,
    currency: row.currency,
  };
}

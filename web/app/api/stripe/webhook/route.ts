import { NextRequest, NextResponse } from 'next/server';
import type Stripe from 'stripe';
import { getStripe, markSessionPaid } from '@/lib/payments';

/** Stripe calls this when a Checkout payment completes; it marks the analysis as paid. */
export async function POST(request: NextRequest) {
  const signature = request.headers.get('stripe-signature');
  const secret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!signature || !secret) {
    return NextResponse.json({ error: 'Missing signature' }, { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = getStripe().webhooks.constructEvent(await request.text(), signature, secret);
  } catch (error) {
    console.error('Invalid Stripe webhook signature:', error);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  try {
    if (
      event.type === 'checkout.session.completed' ||
      event.type === 'checkout.session.async_payment_succeeded'
    ) {
      await markSessionPaid(event.data.object);
    }
  } catch (error) {
    console.error('Error handling Stripe webhook:', error);
    // A non-2xx answer makes Stripe retry the event later.
    return NextResponse.json({ error: 'Webhook handler failed' }, { status: 500 });
  }

  return NextResponse.json({ received: true });
}

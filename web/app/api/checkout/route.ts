import { auth, currentUser } from '@clerk/nextjs/server';
import { NextRequest, NextResponse } from 'next/server';
import { getDocument, getUser } from '@/lib/db';
import { getDictionary } from '@/lib/i18n/server';
import { ANALYSIS_CURRENCY, ANALYSIS_PRICE_CENTS, createPayment, getStripe } from '@/lib/payments';

/** Starts a Stripe Checkout payment for one analysis of the given document. */
export async function POST(request: NextRequest) {
  try {
    const { userId: clerkId } = await auth();

    if (!clerkId) {
      return NextResponse.json({ success: false, error: 'Unauthorized' }, { status: 401 });
    }

    const user = await getUser(clerkId);

    if (!user) {
      return NextResponse.json({ success: false, error: 'User not found' }, { status: 404 });
    }

    const { documentId } = await request.json();

    if (!documentId) {
      return NextResponse.json(
        { success: false, error: 'Document ID is required' },
        { status: 400 },
      );
    }

    const document = await getDocument(documentId, user.id);

    if (!document) {
      return NextResponse.json({ success: false, error: 'Document not found' }, { status: 404 });
    }

    const { t } = await getDictionary();
    const clerkUser = await currentUser();
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || request.nextUrl.origin;
    const returnUrl = `${appUrl}/dashboard?documentId=${encodeURIComponent(documentId)}`;

    const session = await getStripe().checkout.sessions.create({
      mode: 'payment',
      line_items: [
        {
          quantity: 1,
          price_data: {
            currency: ANALYSIS_CURRENCY,
            unit_amount: ANALYSIS_PRICE_CENTS,
            product_data: {
              name: t.payment.productName,
              description: document.fileName,
            },
          },
        },
      ],
      customer_email: clerkUser?.primaryEmailAddress?.emailAddress || user.email || undefined,
      client_reference_id: user.id,
      metadata: { userId: user.id, documentId },
      locale: 'auto',
      success_url: `${returnUrl}&checkout=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${returnUrl}&checkout=cancelled`,
    });

    await createPayment(user.id, documentId, session.id);

    return NextResponse.json({ success: true, url: session.url });
  } catch (error) {
    console.error('Error creating checkout session:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to start payment' },
      { status: 500 },
    );
  }
}

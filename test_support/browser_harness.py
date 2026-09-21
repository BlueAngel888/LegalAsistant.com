"""Isolated browser-test server. All identity, AI, and payment responses are simulated."""
import os
import tempfile
from types import SimpleNamespace

_state_dir = tempfile.mkdtemp(prefix="legal-assistant-browser-")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_state_dir, "browser.sqlite")
os.environ["SESSION_SECRET"] = "browser-tests-only"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_simulated"
os.environ["OPENAI_API_KEY"] = "sk-test-simulated"

import auth
from flask import make_response, redirect, request, url_for


def _simulated_identity():
    user_id = request.cookies.get("test_identity")
    if not user_id:
        return None
    return {"id": user_id, "session_id": "simulated-session", "email": "browser@example.test"}


auth.get_clerk_user = _simulated_identity

import app as application
import utils.ai_analyzer as ai_analyzer

# DocumentConsistencyAnalyzer is a local regex/rules implementation and makes
# no network calls. It therefore needs no external-boundary stub.

def _simulated_analysis(text, language="en"):
    return (
        "SIMULATED AI ANALYSIS (no external request)\n\n"
        "Document Type: Synthetic legal document\n\n"
        "Recommendation: Review the obligations and dates."
    )


ai_analyzer.analyze_with_gpt4 = _simulated_analysis
application.analyze_with_gpt4 = _simulated_analysis


class _SimulatedStripeSession:
    @staticmethod
    def create(**kwargs):
        analysis_id = kwargs["metadata"]["analysis_id"]
        session_id = "cs_test_simulated_" + analysis_id
        return SimpleNamespace(
            id=session_id,
            url=f"http://127.0.0.1:5001/test-payment-complete?session_id={session_id}",
        )

    @staticmethod
    def retrieve(session_id):
        analysis_id = session_id.removeprefix("cs_test_simulated_")
        return SimpleNamespace(
            id=session_id,
            payment_status="paid",
            metadata={"analysis_id": analysis_id},
        )


application.stripe.api_key = "sk_test_simulated"
application.stripe.checkout.Session = _SimulatedStripeSession
app = application.app
app.config.update(TESTING=True)


@app.get("/test-login")
def test_login():
    response = make_response(redirect(url_for("index")))
    response.set_cookie("test_identity", "simulated-clerk-user", httponly=True, samesite="Lax")
    return response


@app.get("/test-payment-complete")
def test_payment_complete():
    return redirect(url_for("success", session_id=request.args["session_id"]))


if __name__ == "__main__":
    print("SIMULATED TEST HARNESS: Clerk identity, Stripe, and OpenAI; temporary SQLite only.")
    app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
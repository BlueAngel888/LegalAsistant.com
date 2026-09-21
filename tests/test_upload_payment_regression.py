"""End-to-end backend regressions using synthetic documents and simulated boundaries."""
import io
from types import SimpleNamespace

import pytest
from docx import Document
from PyPDF2 import PdfWriter
from PyPDF2._page import PageObject
from PyPDF2.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
)

from test_support import browser_harness as harness

application = harness.application
app = harness.app
db = application.db
DocumentAnalysis = application.DocumentAnalysis
PaymentRecord = application.PaymentRecord


def synthetic_pdf(text):
    writer = PdfWriter()
    page = PageObject.create_blank_page(width=612, height=792)
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
    })
    stream = DecodedStreamObject()
    safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream.set_data(f"BT /F1 12 Tf 72 720 Td ({safe_text}) Tj ET".encode())
    page[NameObject("/Contents")] = writer._add_object(stream)
    writer.add_page(page)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def synthetic_docx(text):
    document = Document()
    document.add_paragraph(text)
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


@pytest.fixture(autouse=True)
def clean_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield


@pytest.fixture
def client():
    client = app.test_client()
    client.set_cookie("test_identity", "simulated-clerk-user")
    return client


def upload(client, files, country="RO", language="en"):
    data = {"document_country": country, "analysis_language": language}
    data["file"] = [(io.BytesIO(content), name) for name, content in files]
    return client.post("/upload", data=data, content_type="multipart/form-data")


def current_record(client):
    with client.session_transaction() as sess:
        analysis_id = sess["analysis_id"]
    with app.app_context():
        record = db.session.get(DocumentAnalysis, analysis_id)
        return analysis_id, record.document_text, record.analysis_result


def grant_free_access(client):
    response = client.post("/free-access", data={"free_code": "LETSGO"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/success")


def test_missing_fields_and_no_files_are_rejected(client):
    response = client.post("/upload", data={}, content_type="multipart/form-data")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

    response = client.post(
        "/upload",
        data={"document_country": "RO", "analysis_language": "en"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert "analysis_id" not in sess


def test_one_txt_file_is_really_extracted_before_checkout(client):
    response = upload(client, [("contract.txt", b"Real synthetic obligation due on 2030-01-01.")])
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/checkout")
    _, text, result = current_record(client)
    assert "Real synthetic obligation" in text
    assert "pending" not in text.lower()
    assert result is None  # no AI before payment


def test_generated_docx_is_really_extracted(client):
    response = upload(
        client,
        [("contract.docx", synthetic_docx("Real generated DOCX obligation and deadline."))],
    )
    assert response.status_code == 302
    _, text, _ = current_record(client)
    assert "Real generated DOCX obligation" in text


def test_corrupt_pdf_is_rejected_without_creating_analysis(client):
    response = upload(client, [("corrupt.pdf", b"%PDF-1.4\nnot a valid PDF")])
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as sess:
        assert "analysis_id" not in sess
    with app.app_context():
        assert DocumentAnalysis.query.count() == 0


def test_three_mixed_files_use_real_format_aware_extraction(client):
    files = [
        ("first.txt", b"FIRST synthetic clause"),
        ("second.pdf", synthetic_pdf("SECOND PDF synthetic clause")),
        ("third.txt", b"THIRD synthetic clause"),
    ]
    response = upload(client, files)
    assert response.status_code == 302
    _, text, result = current_record(client)
    assert all(value in text for value in ("FIRST synthetic", "SECOND PDF", "THIRD synthetic"))
    assert "INSTANT UPLOAD" not in text
    assert "processing" not in text.lower()
    assert result is None


def test_discount_invalid_valid_and_simulated_checkout_amount(client, monkeypatch):
    upload(client, [("contract.txt", b"Synthetic checkout contract with enough content.")])
    invalid = client.post("/apply-discount", json={"code": "WRONG"})
    assert invalid.json["success"] is False
    valid = client.post("/apply-discount", json={"code": "LETSGO50"})
    assert valid.json["discount_percent"] == 50

    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="cs_test_50", url="https://stripe.invalid/simulated")

    monkeypatch.setattr(application.stripe.checkout.Session, "create", fake_create)
    response = client.post("/create-checkout-session")
    assert response.status_code == 200
    assert captured["line_items"][0]["price_data"]["unit_amount"] == 5000
    with app.app_context():
        assert PaymentRecord.query.one().amount == 5000


def test_standard_checkout_charges_100_euros(client, monkeypatch):
    upload(client, [("contract.txt", b"Synthetic standard price contract with obligations.")])
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="cs_test_standard", url="https://stripe.invalid/simulated")

    monkeypatch.setattr(application.stripe.checkout.Session, "create", fake_create)
    response = client.post("/create-checkout-session")
    assert response.status_code == 200
    price = captured["line_items"][0]["price_data"]
    assert price["unit_amount"] == 10000
    assert price["currency"] == "eur"
    with app.app_context():
        assert PaymentRecord.query.one().amount == 10000


def test_free_access_and_success_render_simulated_ai(client):
    upload(client, [("contract.txt", b"Synthetic free access contract with obligations.")])
    grant_free_access(client)
    response = client.get("/success")
    assert response.status_code == 200
    assert b"SIMULATED AI ANALYSIS" in response.data
    _, _, result = current_record(client)
    assert "SIMULATED AI ANALYSIS" in result


def test_paid_success_requires_and_accepts_simulated_stripe_verification(client):
    upload(client, [("contract.txt", b"Synthetic paid contract with obligations.")])
    checkout = client.post("/create-checkout-session")
    assert checkout.status_code == 200
    with client.session_transaction() as sess:
        stripe_session_id = sess["stripe_session_id"]

    response = client.get("/success", query_string={"session_id": stripe_session_id})
    assert response.status_code == 200
    assert b"SIMULATED AI ANALYSIS" in response.data
    with app.app_context():
        assert DocumentAnalysis.query.one().payment_status == "completed"
        assert PaymentRecord.query.one().status == "completed"


def test_ai_failure_is_not_cached_or_deleted_and_retry_succeeds(client, monkeypatch):
    upload(client, [("contract.txt", b"Synthetic retry contract retaining source text.")])
    grant_free_access(client)
    calls = {"count": 0}

    def flaky_analyzer(text, language):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("simulated provider outage")
        return "SIMULATED RETRY SUCCESS"

    monkeypatch.setattr(harness.ai_analyzer, "analyze_with_gpt4", flaky_analyzer)
    first = client.get("/success")
    assert first.status_code == 200
    analysis_id, text, result = current_record(client)
    assert "retaining source text" in text
    assert result is None

    second = client.get("/success")
    assert second.status_code == 200
    assert b"SIMULATED RETRY SUCCESS" in second.data
    with app.app_context():
        record = db.session.get(DocumentAnalysis, analysis_id)
        assert "SIMULATED RETRY SUCCESS" in record.analysis_result
        assert record.document_text.startswith("[GDPR_DELETED_")


def test_legacy_cached_background_ai_error_is_retried(client):
    upload(client, [("contract.txt", b"Synthetic legacy error contract retaining source.")])
    analysis_id, _, _ = current_record(client)
    with app.app_context():
        record = db.session.get(DocumentAnalysis, analysis_id)
        record.analysis_result = "AI Analysis Error: old background provider failure"
        db.session.commit()
    grant_free_access(client)

    response = client.get("/success")
    assert response.status_code == 200
    assert b"SIMULATED AI ANALYSIS" in response.data
    with app.app_context():
        result = db.session.get(DocumentAnalysis, analysis_id).analysis_result
        assert "old background provider failure" not in result
        assert "SIMULATED AI ANALYSIS" in result


def test_new_regular_upload_clears_stale_access_and_analysis_type(client):
    with client.session_transaction() as sess:
        sess.update({
            "payment_status": "free_access",
            "free_access": True,
            "discount_code": "LETSGO",
            "discount_percent": 100,
            "analysis_type": "fine",
            "fine_type": "traffic",
        })
    upload(client, [("regular.txt", b"Synthetic regular document with enough content.")])
    with client.session_transaction() as sess:
        for stale_key in (
            "payment_status", "free_access", "discount_code",
            "discount_percent", "analysis_type", "fine_type",
        ):
            assert stale_key not in sess


def test_unauthorized_and_payment_url_bypass_are_blocked(client):
    upload(client, [("contract.txt", b"Synthetic protected contract with terms.")])
    anonymous = app.test_client()
    unauthorized = anonymous.get("/success")
    assert unauthorized.status_code == 302
    assert "/sign-in" in unauthorized.headers["Location"]

    bypass = client.get("/success")
    assert bypass.status_code == 302
    assert bypass.headers["Location"].endswith("/checkout")
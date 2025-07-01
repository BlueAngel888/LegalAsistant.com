#!/usr/bin/env python3
"""
Comprehensive test suite for Legal Assistant application
Tests all major functionality including file upload, payment processing, AI analysis, and chat system
"""

import os
import sys
import unittest
import tempfile
import json
import time
from unittest.mock import patch, MagicMock
from io import BytesIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import DocumentAnalysis, User, PaymentRecord
from utils.ai_analyzer import analyze_with_gpt4, get_document_summary, get_legal_chat_response
from utils.document_consistency_analyzer import DocumentConsistencyAnalyzer
from utils.comprehensive_legal_database import ComprehensiveLegalDatabase

class LegalAssistantTestCase(unittest.TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

class TestRoutes(LegalAssistantTestCase):
    """Test all Flask routes"""
    
    def test_index_route(self):
        """Test main index page"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Legal Assistant', response.data)
    
    def test_language_setting(self):
        """Test language switching"""
        response = self.client.post('/set-language', data={'language': 'ro'})
        self.assertEqual(response.status_code, 302)
        
        # Test with invalid language
        response = self.client.post('/set-language', data={'language': 'invalid'})
        self.assertEqual(response.status_code, 302)
    
    def test_checkout_route(self):
        """Test checkout page access"""
        with self.client.session_transaction() as sess:
            sess['document_text'] = 'Test document content'
            sess['file_names'] = ['test.pdf']
        
        response = self.client.get('/checkout')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'checkout', response.data.lower())
    
    def test_checkout_without_document(self):
        """Test checkout redirect when no document"""
        response = self.client.get('/checkout')
        self.assertEqual(response.status_code, 302)
    
    def test_discount_code_application(self):
        """Test discount code functionality"""
        with self.client.session_transaction() as sess:
            sess['document_text'] = 'Test document'
        
        # Test valid discount code
        response = self.client.post('/apply-discount', 
                                  data=json.dumps({'discount_code': 'letsgo'}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['discount_percent'], 100)
        
        # Test 50% discount code
        response = self.client.post('/apply-discount', 
                                  data=json.dumps({'discount_code': 'letsgo50'}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['discount_percent'], 50)
        
        # Test invalid discount code
        response = self.client.post('/apply-discount', 
                                  data=json.dumps({'discount_code': 'invalid'}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

class TestFileUpload(LegalAssistantTestCase):
    """Test file upload functionality"""
    
    def create_test_pdf(self):
        """Create a test PDF file"""
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test legal document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
        return BytesIO(pdf_content)
    
    def test_file_upload_validation(self):
        """Test file upload validation"""
        # Test without files
        response = self.client.post('/upload-file')
        self.assertEqual(response.status_code, 400)
        
        # Test with valid file
        test_file = self.create_test_pdf()
        response = self.client.post('/upload-file', data={
            'files': [(test_file, 'test.pdf')],
            'country': 'ro',
            'language': 'ro'
        })
        self.assertEqual(response.status_code, 302)
    
    def test_file_size_validation(self):
        """Test file size limits"""
        # Create oversized file (simulate)
        large_content = b'a' * (25 * 1024 * 1024)  # 25MB
        large_file = BytesIO(large_content)
        
        response = self.client.post('/upload-file', data={
            'files': [(large_file, 'large.txt')],
            'country': 'ro',
            'language': 'ro'
        })
        # Should handle large files appropriately
        self.assertIn(response.status_code, [400, 413])

class TestPaymentProcessing(LegalAssistantTestCase):
    """Test Stripe payment integration"""
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_stripe):
        """Test Stripe checkout session creation"""
        # Mock Stripe response
        mock_stripe.return_value = MagicMock(url='https://checkout.stripe.com/test')
        
        with self.client.session_transaction() as sess:
            sess['document_text'] = 'Test document'
            sess['file_names'] = ['test.pdf']
        
        response = self.client.post('/create-checkout-session')
        self.assertEqual(response.status_code, 303)
    
    def test_payment_success_handling(self):
        """Test payment success page"""
        with self.app.app_context():
            # Create test analysis record
            analysis = DocumentAnalysis(
                session_id='test-session',
                file_names='["test.pdf"]',
                document_text='Test document content',
                stripe_session_id='test-stripe-session'
            )
            db.session.add(analysis)
            db.session.commit()
        
        with self.client.session_transaction() as sess:
            sess['stripe_session_id'] = 'test-stripe-session'
        
        response = self.client.get('/success')
        self.assertEqual(response.status_code, 200)

class TestAIAnalysis(LegalAssistantTestCase):
    """Test AI analysis functionality"""
    
    @patch('utils.ai_analyzer.openai_client')
    def test_analyze_with_gpt4(self, mock_openai):
        """Test GPT-4 analysis function"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test analysis result"
        mock_openai.chat.completions.create.return_value = mock_response
        
        result = analyze_with_gpt4("Test document content", "ro")
        self.assertIsInstance(result, str)
        self.assertIn("analysis", result.lower())
    
    @patch('utils.ai_analyzer.openai_client')
    def test_document_summary(self, mock_openai):
        """Test document summary generation"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Contract between parties A and B"
        mock_openai.chat.completions.create.return_value = mock_response
        
        result = get_document_summary("Test contract content")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
    
    @patch('utils.ai_analyzer.openai_client')
    def test_legal_chat_response(self, mock_openai):
        """Test legal chat functionality"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Based on your document analysis..."
        mock_openai.chat.completions.create.return_value = mock_response
        
        result = get_legal_chat_response(
            "What are my obligations?",
            "Contract analysis context",
            [],
            "ro"
        )
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

class TestLegalChat(LegalAssistantTestCase):
    """Test legal chat system"""
    
    @patch('utils.ai_analyzer.get_legal_chat_response')
    def test_legal_chat_endpoint(self, mock_chat):
        """Test legal chat API endpoint"""
        mock_chat.return_value = "Test response from AI"
        
        with self.client.session_transaction() as sess:
            sess['has_document'] = True
        
        response = self.client.post('/legal-chat',
                                  data=json.dumps({
                                      'message': 'Test question',
                                      'analysis_context': 'Test context',
                                      'conversation_history': []
                                  }),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('response', data)
    
    def test_chat_without_document(self):
        """Test chat access without document"""
        response = self.client.post('/legal-chat',
                                  data=json.dumps({'message': 'Test'}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 403)

class TestDocumentConsistency(LegalAssistantTestCase):
    """Test document consistency analyzer"""
    
    def test_consistency_analyzer(self):
        """Test document consistency analysis"""
        analyzer = DocumentConsistencyAnalyzer()
        
        documents = [
            {
                'filename': 'contract1.pdf',
                'text': 'Contract between Company A and Company B dated 2024-01-15',
                'size': 1000
            },
            {
                'filename': 'addendum1.pdf',
                'text': 'Addendum to contract Company A and Company B dated 2024-02-01',
                'size': 500
            }
        ]
        
        result = analyzer.analyze_document_consistency(documents)
        
        self.assertIsInstance(result, dict)
        self.assertIn('consistency_score', result)
        self.assertIn('warnings', result)
        self.assertIn('summary', result)

class TestLegalDatabase(LegalAssistantTestCase):
    """Test comprehensive legal database"""
    
    def test_database_initialization(self):
        """Test legal database initialization"""
        db_instance = ComprehensiveLegalDatabase()
        self.assertIsInstance(db_instance, ComprehensiveLegalDatabase)
    
    def test_country_laws_loading(self):
        """Test country-specific laws loading"""
        db_instance = ComprehensiveLegalDatabase()
        
        # Test Romania
        ro_laws = db_instance.learn_country_laws('ro')
        self.assertIsInstance(ro_laws, dict)
        self.assertIn('civil_code', ro_laws)
        
        # Test Germany
        de_laws = db_instance.learn_country_laws('de')
        self.assertIsInstance(de_laws, dict)
        self.assertIn('civil_code', de_laws)
    
    def test_case_similarity_search(self):
        """Test similar case finding"""
        db_instance = ComprehensiveLegalDatabase()
        
        similar_cases = db_instance.find_similar_cases(
            "Employment contract dispute",
            "ro",
            "contract"
        )
        
        self.assertIsInstance(similar_cases, list)

class TestDatabaseModels(LegalAssistantTestCase):
    """Test database models"""
    
    def test_document_analysis_model(self):
        """Test DocumentAnalysis model"""
        with self.app.app_context():
            analysis = DocumentAnalysis(
                session_id='test-session',
                file_names='["test.pdf"]',
                document_text='Test document content',
                language='ro'
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            retrieved = DocumentAnalysis.query.filter_by(session_id='test-session').first()
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.language, 'ro')
    
    def test_payment_record_model(self):
        """Test PaymentRecord model"""
        with self.app.app_context():
            # First create an analysis
            analysis = DocumentAnalysis(
                session_id='test-session',
                file_names='["test.pdf"]',
                document_text='Test content'
            )
            db.session.add(analysis)
            db.session.commit()
            
            # Then create payment record
            payment = PaymentRecord(
                stripe_session_id='test-stripe-session',
                document_analysis_id=analysis.id,
                amount=1500,
                currency='EUR'
            )
            
            db.session.add(payment)
            db.session.commit()
            
            retrieved = PaymentRecord.query.filter_by(stripe_session_id='test-stripe-session').first()
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.amount, 1500)

class TestSecurityFeatures(LegalAssistantTestCase):
    """Test security features"""
    
    def test_session_security(self):
        """Test session handling security"""
        with self.client.session_transaction() as sess:
            sess['test_key'] = 'test_value'
        
        # Test session persistence
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_input_validation(self):
        """Test input validation"""
        # Test malicious input in chat
        response = self.client.post('/legal-chat',
                                  data=json.dumps({
                                      'message': '<script>alert("xss")</script>',
                                      'analysis_context': 'test'
                                  }),
                                  content_type='application/json')
        
        # Should handle without errors
        self.assertIn(response.status_code, [200, 400, 403])

class TestErrorHandling(LegalAssistantTestCase):
    """Test error handling"""
    
    def test_404_error(self):
        """Test 404 error handling"""
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_json_request(self):
        """Test invalid JSON handling"""
        response = self.client.post('/legal-chat',
                                  data='invalid json',
                                  content_type='application/json')
        
        self.assertIn(response.status_code, [400, 403])

class TestPerformance(LegalAssistantTestCase):
    """Test performance aspects"""
    
    def test_response_times(self):
        """Test basic response times"""
        start_time = time.time()
        response = self.client.get('/')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 2.0)  # Should respond within 2 seconds
    
    def test_database_performance(self):
        """Test database query performance"""
        with self.app.app_context():
            # Create multiple records
            for i in range(10):
                analysis = DocumentAnalysis(
                    session_id=f'test-session-{i}',
                    file_names=f'["test{i}.pdf"]',
                    document_text=f'Test document content {i}'
                )
                db.session.add(analysis)
            
            db.session.commit()
            
            # Test query performance
            start_time = time.time()
            results = DocumentAnalysis.query.all()
            end_time = time.time()
            
            self.assertEqual(len(results), 10)
            self.assertLess(end_time - start_time, 1.0)

def run_all_tests():
    """Run all tests and generate report"""
    print("=" * 60)
    print("LEGAL ASSISTANT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    test_classes = [
        TestRoutes,
        TestFileUpload,
        TestPaymentProcessing,
        TestAIAnalysis,
        TestLegalChat,
        TestDocumentConsistency,
        TestLegalDatabase,
        TestDatabaseModels,
        TestSecurityFeatures,
        TestErrorHandling,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('\n')[-2]}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
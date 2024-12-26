# test_integration.py
import unittest
import boto3
from moto import mock_aws
from authcallback import app as auth_app
import json
import logging
from unittest.mock import patch
from s3_manager import SecretsManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Mock secrets for testing
MOCK_SECRETS = {
    'AUTH0_DOMAIN': 'test.auth0.com',
    'AUTH0_AUDIENCE': 'test-audience',
    'REGION_NAME': 'us-east-2',
    'INPUT_AUDIO_BUCKET': 'test-bucket',
    'TRANSCRIBED_BUCKET': 'test-transcribed-bucket'
}

@mock_aws
class TestIntegration(unittest.TestCase):
    def setUp(self):
        logger.info("Setting up test environment...")
        # Set up mock secrets
        SecretsManager._secrets = MOCK_SECRETS
        
        auth_app.config['TESTING'] = True
        auth_app.config['SECRET_KEY'] = 'test-key'  # Required for sessions
        self.app = auth_app.test_client()
        
        try:
            # Create test bucket
            logger.info("Creating test bucket...")
            self.s3_client = boto3.client('s3', region_name='us-east-2')
            self.s3_client.create_bucket(
                Bucket=MOCK_SECRETS['INPUT_AUDIO_BUCKET'],
                CreateBucketConfiguration={'LocationConstraint': 'us-east-2'}
            )
            logger.info("Test setup completed successfully")
        except Exception as e:
            logger.error(f"Error in setup: {str(e)}")
            raise

    @patch('authcallback.oauth.oidc.authorize_access_token')
    def test_auth_s3_integration(self, mock_authorize):
        logger.info("Starting auth/S3 integration test...")
        try:
            # Mock the OAuth token response
            mock_token = {
                'userinfo': {
                    'sub': 'test123',
                    'email': 'test@example.com',
                    'custom:userType': 'customer'
                }
            }
            mock_authorize.return_value = mock_token

            # Simulate the OAuth callback
            response = self.app.get('/auth/callback')
            logger.info(f"Auth response status: {response.status_code}")
            self.assertEqual(response.status_code, 302)  # Should redirect

            # Check the session
            with self.app.session_transaction() as sess:
                self.assertIn('user', sess)
                user_id = sess['user']['sub']
                user_type = sess['user'].get('custom:userType', 'customer')

            # Test S3 path construction
            test_key = f"users/{user_type}/{user_id}/test.txt"
            
            logger.info(f"Testing S3 upload to path: {test_key}")
            # Test uploading to constructed path
            self.s3_client.put_object(
                Bucket=MOCK_SECRETS['INPUT_AUDIO_BUCKET'],
                Key=test_key,
                Body='test content'
            )

            # Verify object exists
            logger.info("Verifying uploaded object...")
            response = self.s3_client.get_object(
                Bucket=MOCK_SECRETS['INPUT_AUDIO_BUCKET'],
                Key=test_key
            )
            
            content = response['Body'].read().decode()
            logger.info(f"Retrieved content: {content}")
            self.assertEqual(content, 'test content')
                
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            raise

if __name__ == '__main__':
    unittest.main()

import os

# Stripe Configuration
STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", "pk_test_default")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "sk_test_default")

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-default")

# Application Configuration
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'jpg', 'jpeg', 'png'}

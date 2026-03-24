# tests/conftest.py
import pytest
import os

os.environ["GITHUB_TOKEN"] = "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"
os.environ["GITHUB_WEBHOOK_SECRET"] = "secret123"
os.environ["GROQ_API_KEY"] = "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"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JENKINS_URL"] = ""
os.environ["APP_ENV"] = "test"
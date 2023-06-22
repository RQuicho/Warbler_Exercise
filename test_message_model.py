"""Message model tests."""

import os
from unittest import TestCase
from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(self):
    """Test views for messages."""

    def setUp(self):
        """clear any existing data from database."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_message_model(self):
        """Does basic model work?"""

        msg = Message(
            text="Test message",
            timestamp='2017-01-21 11:04:53.522807',
            user_id=1
        )

        db.session.add(msg)
        db.session.commit()

        

    

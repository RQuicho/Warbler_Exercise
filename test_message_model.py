"""Message model tests."""

import os
from unittest import TestCase
from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        u = User.signup('user', 'user@email.com', 'password', None)
        uid = 111
        u.id = uid
        db.session.commit()

        u = User.query.get(uid)

        self.u = u
        self.uid = uid

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model work?"""

        msg = Message(
            text="Test message",
            user_id=self.uid
        )

        db.session.add(msg)
        db.session.commit()

        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, 'Test message')

    def test_message_like(self):
        msg1 = Message(
            text="Testing likes",
            user_id=self.uid
        )

        db.session.add(msg1)
        db.session.commit()

        self.u.likes.append(msg1)
        db.session.commit()

        l = Likes.query.filter(Likes.user_id == self.uid).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, msg1.id)

    

    

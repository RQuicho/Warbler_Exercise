"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        u1 = User.signup('user1', 'user1@email.com', 'password', None)
        uid1 = 111
        u1.id = uid1

        u2 = User.signup('user2', 'user2@email.com', 'password2', None)
        uid2 = 222
        u2.id = uid2

        db.session.commit()

        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)

        self.u1 = u1
        self.uid1 = uid1
        self.u2 = u2
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    ##### Following Tests #################################

    def test_user_follows(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u1.followers), 0)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)

    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))


    ##### Signup Tests #################################

    def test_valid_signup(self):
        u3 = User.signup('testUser', 'test@email.com', 'testpassword', None)
        uid3 = 333
        u3.id = uid3
        db.session.commit()

        u3 = User.query.get(uid3)

        self.assertIsNotNone(u3)
        self.assertEqual(u3.username, 'testUser')
        self.assertEqual(u3.email, 'test@email.com')
        self.assertIn('$2b', u3.password)

    def test_invalid_username_signup(self):
        u4 = User.signup(None, 'invalid@email.com', 'password', None)
        uid4 = 4444
        u4.id = uid4
        with self.assertRaises(IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        u4 = User.signup('email', None, 'password', None)
        uid4 = 4444
        u4.id = uid4
        with self.assertRaises(IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup('testuser', 'test@email.com', None, None)

        
    ##### Authentication Tests #################################

    def test_valid_auth(self):
        self.assertTrue(User.authenticate(self.u1.username, 'password'))

    def test_invalid_username(self):
        self.assertFalse(User.authenticate('wrong', 'password'))

    def test_invalid_password(self):
        self.assertFalse(User.authenticate('user1', 'wrong'))
      



        


        




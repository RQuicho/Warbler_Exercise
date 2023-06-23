"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 1234
        self.testuser.id = self.testuser_id

        self.u1 = User.signup('user1', 'u1@email.com', 'password', None)
        self.u1_id = 123
        self.u1.id = self.u1_id

        self.u2 = User.signup('user2', 'u2@email.com', 'password', None)
        self.u2_id = 456
        self.u2.id = self.u2_id

        self.u3 = User.signup('user3', 'u3@email.com', 'password', None)
        self.u3_id = 789
        self.u3.id = self.u3_id

        self.u4 = User.signup('user4', 'u4@email.com', 'password', None)
        self.u4_id = 135
        self.u4.id = self.u4_id

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_user_home(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn('testuser', str(resp.data))
            self.assertIn('user1', str(resp.data))
            self.assertIn('user2', str(resp.data))
            self.assertIn('user3', str(resp.data))
            self.assertIn('user4', str(resp.data))

    def test_user_search(self):
        with self.client as c:
            resp = c.get('/users?q=test')

            self.assertIn('testuser', str(resp.data))

            self.assertNotIn('user1', str(resp.data))
            self.assertNotIn('user2', str(resp.data))
            self.assertNotIn('user3', str(resp.data))
            self.assertNotIn('user4', str(resp.data))

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser', str(resp.data))

    def setup_likes(self):
        m1 = Message(text='tes1likes msg', user_id=self.testuser_id)
        m2 = Message(text='test2likes msg', user_id=self.testuser_id)
        m3 = Message(id=2468, text='tes3likes msg', user_id=self.u1_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        like = Likes(user_id=self.testuser_id, message_id=2468)
        db.session.add(like)
        db.session.commit()

    def test_user_show_likes(self):
        self.setup_likes()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn('testuser', str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all('li', {'class': 'stat'})
            self.assertEqual(len(found), 4)

            self.assertIn('2', found[0].text) # count 2 messages
            self.assertIn('0', found[1].text) # count 0 followers
            self.assertIn('0', found[2].text) # count 0 following
            self.assertIn('1', found[3].text) # count 1 like

    def test_user_add_likes(self):
        m = Message(id=444, text='add like', user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.post(f'/messages/444/like', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            likes = Likes.query.filter(Likes.message_id == 444).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_remove_likes(self):
        self.setup_likes()

        m = Message.query.filter(Message.text == 'tes3likes msg').one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser_id)

        l = Likes.query.filter(Likes.user_id == self.testuser_id and Likes.message_id == m.id).one()
        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id == m.id).all()
            self.assertEqual(len(likes), 0)
            
    def test_unauth_likes(self):
        self.setup_likes()

        m = Message.query.filter(Message.text == 'tes3likes msg').one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))

            self.assertEqual(like_count, Likes.query.count())

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1, f2, f3])
        db.session.commit()

    def test_show_user_follows(self):
        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn('testuser', str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all('li', {'class': 'stat'})
            self.assertEqual(len(found), 4)

            self.assertIn('0', found[0].text) # count 0 messages
            self.assertIn('2', found[1].text) # count 2 following
            self.assertIn('1', found[2].text) # count 1 follower
            self.assertIn('0', found[3].text) # count 0 like

    def test_show_user_following(self):
        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/users/{self.testuser_id}/following")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('user1', str(resp.data))
            self.assertIn('user2', str(resp.data))
            self.assertNotIn('user3', str(resp.data))
            self.assertNotIn('user4', str(resp.data))

    def test_show_user_followers(self):
        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/users/{self.testuser_id}/followers")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('user1', str(resp.data))
            self.assertNotIn('user2', str(resp.data))
            self.assertNotIn('user3', str(resp.data))
            self.assertNotIn('user4', str(resp.data))

    def test_unauth_following(self):
        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))

    def test_unauth_followers(self):
        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))









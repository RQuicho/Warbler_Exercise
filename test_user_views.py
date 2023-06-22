    def test_user_repr(self):
        """Does repr function return correct info."""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u.__repr__(self)

        self.assertEqual(f"<User #{self.id}: {self.username}, {self.email}>", '<User #1: testuser, test@test.com>')

    # def test_user_is_following(self):
    #     """Does function show if the current user is following another user?"""
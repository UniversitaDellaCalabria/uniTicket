from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from chat.models import ChatMessageModel


class ChatApiMethodsTest(TestCase):
    """
    Checks that the chat API exposes only the actions used by the frontend
    """

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="user", password="x")
        self.other_user = user_model.objects.create_user(username="other_user",
                                                         password="x")
        self.third_user = user_model.objects.create_user(username="third_user",
                                                         password="x")
        # message between two other users
        self.msg = ChatMessageModel.objects.create(user=self.other_user,
                                                   recipient=self.third_user,
                                                   room="room",
                                                   body="hello")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_user_cannot_be_deleted(self):
        response = self.client.delete(f"/api/chat/user/{self.other_user.pk}/")
        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            get_user_model().objects.filter(pk=self.other_user.pk).exists()
        )

    def test_user_cannot_be_partially_updated(self):
        response = self.client.patch(f"/api/chat/user/{self.other_user.pk}/",
                                     {"room": "room"})
        self.assertEqual(response.status_code, 405)

    def test_users_cannot_be_listed_or_created(self):
        self.assertEqual(self.client.get("/api/chat/user/").status_code, 404)
        self.assertEqual(self.client.post("/api/chat/user/", {}).status_code, 404)

    def test_message_cannot_be_updated_or_deleted(self):
        url = f"/api/chat/message/{self.msg.pk}/"
        self.assertEqual(self.client.patch(url, {"body": "edited"}).status_code, 405)
        self.assertEqual(self.client.put(url, {"body": "edited"}).status_code, 405)
        self.assertEqual(self.client.delete(url).status_code, 405)
        self.msg.refresh_from_db()
        self.assertEqual(self.msg.body, "hello")

    def test_frontend_actions(self):
        # messages list
        response = self.client.get("/api/chat/message/?room=room")
        self.assertEqual(response.status_code, 200)
        # new message
        response = self.client.post("/api/chat/message/",
                                    {"recipient": self.other_user.pk,
                                     "room": "room",
                                     "body": "hi",
                                     "broadcast": False})
        self.assertEqual(response.status_code, 201)
        # own user detail
        response = self.client.get(f"/api/chat/user/{self.user.pk}/")
        self.assertEqual(response.status_code, 200)
        # chat status toggle (PUT form data, like chat/static/js/app.js)
        response = self.client.put(f"/api/chat/user/{self.user.pk}/",
                                   "room=room",
                                   content_type="application/x-www-form-urlencoded")
        self.assertEqual(response.status_code, 200)

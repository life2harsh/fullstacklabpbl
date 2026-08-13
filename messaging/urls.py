from django.urls import path

from . import views

urlpatterns = [
    path("chat/", views.chat_page, name="chat"),
    path("messages", views.send_message, name="send-message"),
    path("messages/conversations", views.conversations, name="conversations"),
    path("messages/conversation/<int:other_user_id>", views.clear_conversation, name="clear-conversation"),
    path("messages/<int:identifier>", views.message_or_conversation, name="message-or-conversation"),
]

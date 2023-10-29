import json

from django.test import TestCase
from django.db.models import signals
from django.dispatch import Signal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from App import models


User = get_user_model()

def disconnect_signals(model):
    all_signals_names = filter(lambda i: i.startswith('post') or i.startswith('pre'), dir(signals))
    all_signals = map(lambda name: getattr(signals, name), all_signals_names)

    for signal in all_signals:
        for receiver_func in Signal._live_receivers(signal, sender=model):
            signal.disconnect(receiver_func, sender=model)

def create_user():
    user = User.objects.create_user(username='testuser', email='testuser@gmail.com', password='password123')
    return user


class BookmarkFileTestCase(TestCase):
    model = models.BookmarkFile

    def setUp(self) -> None:
        disconnect_signals(self.model)
        user = create_user()

        url = 'https://quotes.toscrape.com/'
        urls = [url]
        html_content = f'''
            <!DOCTYPE NETSCAPE-Bookmark-file-1><TITLE>Bookmarks</TITLE><H1>Bookmarks Menu</H1>
            <DL><p>
                <DT><A HREF="{url}" ADD_DATE="1691177552" LAST_MODIFIED="1691177552" ICON_URI="https://xds.com/" ICON="xxxx">Text title</A>
            </DL><p>
        '''

        json_file = SimpleUploadedFile("test_file.json", json.dumps(urls, ensure_ascii=False).encode('utf8'))
        html_file = SimpleUploadedFile("test_file.html", html_content.encode('utf8'))
        text_file = SimpleUploadedFile("test_file.txt", b'wrong content')

        self.html_obj = models.BookmarkFile.objects.create(
            user=user, location=json_file,    
        )
        # self.json_obj = models.BookmarkFile.objects.create()

    def test_your_model(self):
        print('Supe hard logic', self.html_obj.location.path)
        # Your test logic without signals here

import factory
import random

from django.contrib.auth import get_user_model

from App import models

User = get_user_model()

username_prefix = 0
def generate_username(*args):
    global username_prefix

    username_prefix += 1
    return 'user_' + str(username_prefix)

def generate_email(*args):
    global username_prefix

    username_prefix += 1
    return 'user_' + str(username_prefix) + '@example.com'




class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyAttribute(generate_username)
    email = factory.LazyAttribute(generate_email)
    password = factory.Faker('password')


class BookmarkFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.BookmarkFile

    user = factory.SubFactory(UserFactory)
    location = factory.django.FileField()


class WebsiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Website

    user = factory.SubFactory(UserFactory)
    domain = factory.Faker('url')
    favicon = factory.Faker('url')


class BookmarkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Bookmark

    user = factory.SubFactory(UserFactory)
    website = factory.SubFactory(WebsiteFactory)

    url = factory.Faker('url')
    title = factory.Faker('sentence')

    process_status = factory.Iterator([60,70,80])
    favorite = factory.Faker('boolean')
    hidden = factory.Faker('boolean')

    # added_at = factory.Faker('date_time')


class BookmarkHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.BookmarkHistory

    bookmark = factory.SubFactory(BookmarkFactory)


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Tag

    user = factory.SubFactory(UserFactory)
    name = factory.Faker('word')
    bookmarks = factory.RelatedFactory('App.factories.BookmarkFactory', 'tags')
    weight = factory.Faker('pyint')


class GraphNodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.GraphNode

    user = factory.SubFactory(UserFactory)
    bookmarks = factory.RelatedFactory(
        'App.factories.BookmarkFactory', 'nodes')

    name = factory.Faker('word')
    path = factory.Faker('word')

    threshold = factory.Faker('pyfloat')
    is_leaf = factory.Faker('boolean')


class WordWeightFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.WordWeight

    bookmark = factory.SubFactory('App.factories.BookmarkFactory')
    word = factory.Faker('word')
    weight = factory.Faker('pyint')
    important = factory.Faker('boolean')


class ScrapyResponseLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ScrapyResponseLog

    bookmark = factory.SubFactory('App.factories.BookmarkFactory')
    status_code = factory.Iterator([200, 404, 500, 403, 503, 400])


USERS_COUNT = 1_00
MIN_BOOKMARKS_PER_USER = 300
MAX_BOOKMARKS_PER_USER = 10_000


def create_test_data():
    for _ in range(USERS_COUNT):
        try:
            user = UserFactory.create()
            print(f'{user=}')

            bookmarks_count = random.randint(MIN_BOOKMARKS_PER_USER, MAX_BOOKMARKS_PER_USER)
            bookmarks = BookmarkFactory.create_batch(bookmarks_count, user=user)
            # tags = BookmarkFactory.create_batch(random.randint(1, 100), user=user)
            print(f'{bookmarks_count=}')
            for bookmark in bookmarks:
                print(f'{bookmark=}')
                if random.randint(1, 10) == 3:
                    BookmarkHistoryFactory.create(bookmark=bookmark)

                # probability 70% to have tags
                # if random.randint(1, 10) <= 7:
                #     # choose random tags from tags list
                #     tags_count = random.randint(1, 10)
                #     TagFactory.create(bookmarks=[bookmark],
                #             tags=random.sample(tags, tags_count))

                words_count = random.randint(10, 50)
                WordWeightFactory.create_batch(words_count, bookmark=bookmark)

                ScrapyResponseLogFactory(bookmark=bookmark)

            print('---'*3)
        except Exception as e:
            print(e)
            continue

DJANGO_SHELL = 'django.core.management.commands.shell'
if __name__ in ["__main__", DJANGO_SHELL]:
    create_test_data()

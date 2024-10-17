import datetime
import itertools
import random
import string

from django.utils import timezone

from App import models


class DataFactory:
    INCREMENT = itertools.count().__next__

    def word(self):
        space = string.ascii_lowercase
        length = random.randint(3, 22)
        letters = random.choices(space, k=length)
        return "".join(letters)

    def phrase(self):
        length = random.randint(1, 16)
        words = [self.word() for _ in range(length)]
        return " ".join(words)

    def username(self):
        word = f"{self.word()}_{self.word()}"
        return f"{word}_{self.INCREMENT()}"

    def email(self):
        return self.username() + "@example.com"

    def password(self):
        length = random.randint(8, 16)
        space = string.ascii_letters + string.digits
        letters = random.choices(space, k=length)
        return "".join(letters)

    def boolean(self):
        return random.choice([True, False])

    def url(self):
        return f"https://{self.word()}.com/{self.word()}/?x={self.word()}"

    def domain(self):
        return f"{self.word()}.com"

    def number(self):
        return random.randint(0, 100)

    def decimal(self):
        return self.number() % 100 / 100

    def choices(self, choices):
        return random.choice(choices)

    def date(self):
        from_how_long = self.number()
        return timezone.now() - datetime.timedelta(days=from_how_long)


data = DataFactory()


def user():
    return models.User(
        username=data.username(),
        email=data.email(),
        password=data.password(),
    )


def website(user):
    return models.Website(
        user=user,
        domain=data.domain(),
        favicon=data.url(),
    )


def bookmark(user, website_instance=None):
    if website_instance is None:
        website_instance = website(user)
        website_instance.save()

    return models.Bookmark(
        user=user,
        website=website_instance,
        url=data.url(),
        title=data.phrase()[:200],
        process_status=data.choices([60, 70, 80]),
        favorite=data.boolean(),
        hidden=data.boolean(),
        added_at=data.date(),
    )


def history(bookmark):
    return models.BookmarkHistory(
        bookmark=bookmark,
    )


def tag(user):
    return models.Tag(
        user=user,
        name=data.word(),
        weight=data.number(),
    )


def tag_with_bookmarks(user, bookmarks):
    instance = tag(user)

    # This is closure
    def _m2m_bookmarks():
        for b in bookmarks:
            instance.bookmarks.add(b)

    return instance, _m2m_bookmarks


def word_weight(bookmark):
    return models.WordWeight(
        bookmark=bookmark,
        word=data.word(),
        weight=data.number(),
        important=data.boolean(),
    )


def scrapy_log(bookmark):
    return models.ScrapyResponseLog(
        bookmark=bookmark,
        status_code=data.choices([200, 404, 500, 403, 503, 400]),
    )


def graph_node(user):
    return models.GraphNode(
        user=user,
        name=data.phrase()[:200],
        path=data.word(),
        is_leaf=data.boolean(),
        threshold=data.decimal(),
    )


def graph_node_with_bookmarks(user, bookmarks):
    instance = graph_node(user)

    # This is closure
    def _m2m_bookmarks():
        for b in bookmarks:
            instance.bookmarks.add(b)

    return instance, _m2m_bookmarks


USERS_COUNT = 100
MIN_BOOKMARKS = 5000
MAX_BOOKMARKS = 10_000


def store_data():
    for _ in range(USERS_COUNT):
        histories = []
        tags = []
        tags_bookmarks = []
        words = []
        scrapy_logs = []
        nodes = []
        nodes_bookmarks = []

        user_instance = user()
        user_instance.save()

        print(f"{_}- {user_instance=}")

        websites_count = random.randint(5, 50)
        websites = [website(user_instance) for _ in range(websites_count)]
        models.Website.objects.bulk_create(websites, batch_size=1000)

        bookmarks_count = random.randint(MIN_BOOKMARKS, MAX_BOOKMARKS)
        bookmarks = [
            bookmark(user_instance, website_instance=random.choice(websites))
            for _ in range(bookmarks_count)
        ]
        models.Bookmark.objects.bulk_create(bookmarks, batch_size=1000)

        print(f"will work on {bookmarks_count} bookmarks")

        for b in bookmarks:
            if random.randint(1, 10) == 1:
                print("create history")
                histories.append(history(b))

            print("create words")
            words_count = random.randint(8, 50)
            words.extend([word_weight(b) for _ in range(words_count)])

            scrapy_logs.append(scrapy_log(b))
        # tag, tag_with_bookmarks
        tags_count = random.randint(8, 100)
        avg_bookmarks_for_tag = bookmarks_count // tags_count
        tags_tuples = [
            tag_with_bookmarks(
                user_instance,
                bookmarks=random.sample(bookmarks, k=avg_bookmarks_for_tag),
            )
            for _ in range(tags_count)
        ]

        tags.extend([t[0] for t in tags_tuples])
        tags_bookmarks.extend([t[1] for t in tags_tuples])

        # graph_node, graph_node_with_bookmarks
        nodes_count = random.randint(12, 200)
        avg_bookmarks_for_node = bookmarks_count // nodes_count
        nodes_tuples = [
            graph_node_with_bookmarks(
                user_instance,
                bookmarks=random.sample(bookmarks, k=avg_bookmarks_for_node),
            )
            for _ in range(nodes_count)
        ]

        nodes.extend([t[0] for t in nodes_tuples])
        nodes_bookmarks.extend([t[1] for t in nodes_tuples])

        print("bulk creates")
        models.BookmarkHistory.objects.bulk_create(histories, batch_size=1000)
        models.Tag.objects.bulk_create(tags, batch_size=1000)
        models.WordWeight.objects.bulk_create(words, batch_size=1000)
        models.ScrapyResponseLog.objects.bulk_create(scrapy_logs, batch_size=1000)
        models.GraphNode.objects.bulk_create(nodes, batch_size=1000)

        for save_m2m in tags_bookmarks + nodes_bookmarks:
            print("m2m2 save")
            save_m2m()
        print("------ user done ------")


DJANGO_SHELL = "django.core.management.commands.shell"
if __name__ in ["__main__", DJANGO_SHELL]:
    store_data()

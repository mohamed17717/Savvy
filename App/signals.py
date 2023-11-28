from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from App import models, tasks


@receiver(post_save, sender=models.BookmarkFile)
def on_create_bookmark_file_extract_urls(sender, instance, created, **kwargs):
    # TODO make location is not editable
    if not created:
        return

    bookmarks = [
        models.Bookmark.instance_by_parent(instance, bookmark)
        for bookmark in instance.bookmarks_links
    ]
    # TODO add batch size or batch the data in the task
    models.Bookmark.objects.bulk_create(bookmarks)
    task = tasks.crawl_bookmarks_task.apply_async(
        kwargs={'bookmark_ids': [bm.id for bm in bookmarks]})

    instance.tasks.append(task.task_id)
    instance.save()


@receiver(pre_save, sender=models.BookmarkFile)
def on_save_bookmark_file_validate_file_content(sender, instance, **kwargs):
    instance.file_obj.validate(raise_exception=True)


@receiver(post_save, sender=models.DocumentWordWeight)
def on_create_word_update_tags(sender, instance, created, **kwargs):
    if created:
        tag, created = models.Tag.objects.get_or_create(
            user=instance.bookmark.user,
            name=instance.word
        )

        print(f'({tag.name}) .. {created=} -> {tag.weight=}, {instance.weight=}')
        # tag.bookmarks.add(instance.bookmark)
        tag.weight += instance.weight
        tag.save()

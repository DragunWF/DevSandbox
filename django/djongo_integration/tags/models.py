from djongo import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from bson.objectid import ObjectId


class TaggedItemManager(models.Manager):
    """
    Customer Query Manager
    """

    def get_tags_for(self, obj_type, obj_id):
        """
        Gets the tags from a product
        """
        content_type = ContentType.objects.get_for_model(obj_type)

        return TaggedItem.objects.select_related("tag").filter(
            content_type=content_type,
            object_id=obj_id
        )


class Tag(models.Model):
    _id = models.IntegerField(primary_key=True)
    label = models.CharField(max_length=255)

    def __str__(self, tag):
        return tag.label


class TaggedItem(models.Model):
    # Overrides the default manager to a custom one
    objects = TaggedItemManager()

    _id = models.IntegerField(primary_key=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    # ContentType : allows the developer to create generic relationships between models
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

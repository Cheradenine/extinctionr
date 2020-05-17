from django import forms
from django.db import models
from django.core.paginator import Paginator

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.admin.edit_handlers import (
    FieldPanel, InlinePanel, MultiFieldPanel, StreamFieldPanel, PageChooserPanel
)
from wagtail.core.blocks import (
    RichTextBlock, BlockQuoteBlock, CharBlock, StructBlock, BooleanBlock, StructValue
)
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField, StreamField
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.models import Image
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from wagtailmarkdown.blocks import MarkdownBlock

from extinctionr.vaquita.blocks import ImageCarouselBlock
from .blocks import EmbedContentBlock

@register_snippet
class StoryCategory(models.Model):
    name = models.CharField(max_length=255)
    panels = [
        FieldPanel('name')
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'story categories'


class StoryTag(TaggedItemBase):
    content_object = ParentalKey(
        'StoryPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


class StoryIndexPage(Page, Orderable):
    STORIES_PER_PAGE = 6

    """The 'media' section of the site will host multiple StoryIndex pages
    Each one is configured to show certain kinds of stories and
    other optional sections we will define."""
    subpage_types = [
        'news.StoryPage'
    ]

    intro = RichTextField(blank=True)

    # determines what type of stories are displayed on this page
    categories = ParentalManyToManyField('news.StoryCategory', blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        FieldPanel('categories', widget=forms.CheckboxSelectMultiple)
    ]

    def get_context(self, request):
        
        context = super().get_context(request)

        
        stories = StoryPage.objects.live() #child_of(self).live()
        stories = stories.order_by('-first_published_at')
        stories = stories.filter(categories__in=list(self.categories.all())).distinct()
        tag = request.GET.get('tag', '')
        if tag:
            stories = stories.filter(tags__name=tag)

        # Pagination.
        paginator = Paginator(stories, self.STORIES_PER_PAGE)
        page = request.GET.get("page")
        try:
            stories = paginator.page(page)
        except:
            stories = paginator.page(1)

        featured = FeaturedStory.objects.all().order_by('-story__first_published_at')
        context['stories'] = stories
        context['featured'] = featured
        context['peer_pages'] = self.get_siblings()

        return context


@register_snippet
class FeaturedStory(models.Model):
    """ A featured story holds a reference to the story and can be set
    in the snippets editor"""
    story = models.ForeignKey(
        "wagtailcore.Page", 
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    panels = [
        PageChooserPanel('story', 'news.StoryPage'),
    ]

    def __str__(self):
        return self.story.title

    class Meta:
        verbose_name_plural = "featured stories"


class StoryPage(Page):
    MAX_RELATED_STORIES = 10

    # This is a leaf page
    subpage_types = []
    parent_page_types = [
        'news.StoryIndexPage'
    ]

    date = models.DateField("post date")
    lede = models.CharField(max_length=1024)
    tags = ClusterTaggableManager(through=StoryTag, blank=True)
    categories = ParentalManyToManyField('news.StoryCategory', blank=True)

    # Add allowed block types to StreamPanel
    content = StreamField(
        [
            ('paragraph', RichTextBlock(features=[
                'h2', 'h3', 'bold', 'italic', 'link', 'ol', 'ul'
            ])),
            ('markdown', MarkdownBlock(icon='code')),
            ('image', StructBlock([
                ('image', ImageChooserBlock()),
                ('caption', CharBlock(required=False))
            ])),
            ('carousel', ImageCarouselBlock()),
            ('quote', BlockQuoteBlock()),
            ('embedded_content', EmbedContentBlock()),
        ]
    )

    def get_context(self, request):
        
        context = super().get_context(request)
        tags_list = list(self.tags.all())
        stories = StoryPage.objects.live().order_by('-first_published_at')
        # Collects set of stories that has the same tags as this story.
        related = stories.filter(tags__in=tags_list)
        related = related.exclude(id=self.id)
        related = related.distinct()[0:self.MAX_RELATED_STORIES]
        if related.count() > 0:
            context["related"] = related

        # get next and previous by date. the names look swapped but this is intentional
        # because posts are sorted in reverse chronological order

        try:
            context['nextstory'] = self.get_previous_by_date(tags__in=tags_list)
        except (StoryPage.DoesNotExist, ValueError):
            pass

        try:
            context['prevstory'] = self.get_next_by_date(tags__in=tags_list)
        except (StoryPage.DoesNotExist, ValueError):
            pass

        return context

    def author(self):
        return self.owner.username

    def hero_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    def media_thumbnail_url(self):
        for child in self.content:
            if child.block.name == 'embedded_content':
                return child.value.thumbnail_url
        return None

    def hero_image_url(self):
        hero_image = self.hero_image()
        if hero_image:
            return hero_image.url
        return self.media_thumbnail_url()
        
    search_fields = Page.search_fields = [
        index.SearchField('lede'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('date'),
            FieldPanel('tags'),
            FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
        ]),
        FieldPanel('lede'),
        InlinePanel('gallery_images', label="Gallery Images"),
        StreamFieldPanel('content')
    ]


class StoryPageGalleryImage(Orderable):
    page = ParentalKey(StoryPage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'vaquita.CustomImage', on_delete=models.CASCADE, related_name="+"
    )
    caption = models.CharField(blank=True, max_length=250)
    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption')
    ]

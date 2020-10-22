from datetime import timedelta
from dateutil import tz

from django import template
from django.utils.html import strip_tags
from django.utils.http import urlquote_plus
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.text import Truncator
from html.parser import HTMLParser

from extinctionr.actions import models
from markdownx.utils import markdownify

register = template.Library()


@register.inclusion_tag('recent_actions.html')
def recent_actions(*args, **kwargs):
    adverb = kwargs.get('adverb', 'recent')
    ract = models.Action.objects.filter(public=True)
    if adverb == 'recent':
        ract = ract.filter(when__lte=now()).order_by('-when')
    else:
        ract = ract.filter(when__gte=now()).order_by('when')
    return {'actions': ract[:10], 'adverb': adverb.capitalize()}


@register.inclusion_tag('highlight_action.html')
def highlight_action(*args, **kwargs):
    try:
        action = models.Action.objects.filter(public=True, tags__name='highlight', when__gte=now())[0]
    except IndexError:
        action = None
    return {'action': action}


# Need to pull the href attribute out of the link.
class HrefExtractor(HTMLParser):
    def __init__(self, link_tag):
        super().__init__()
        self.href = None
        self.feed(link_tag)

    def handle_starttag(self, tag, attrs):
        if tag == "a" and self.href is None:
            hrefs = [val for name, val in attrs if name == "href"]
            self.href = hrefs[0]


@register.simple_tag(name='calendar_url', takes_context=True)
def calendar_url(context, action, service):
    def action_localtime(action, tz_name):
        timezone = tz.gettz(tz_name)
        return action.when.astimezone(timezone)

    def action_desc(action, full_url):
        desc = markdownify(strip_tags(action.description))
        desc = Truncator(desc).words(30, html=True, truncate=' …')
        desc += f"<p><br><a href=\"{full_url}\">Full Event Details</a></p>"
        desc = urlquote_plus(desc)
        return desc

    def action_loc(action):
        href = HrefExtractor(action.location_link).href
        return urlquote_plus(href)

    def action_times(action, tfmt):
        action_start = action_localtime(action, tzname)
        start = action_start.strftime(tfmt)
        end = (action_start + timedelta(hours=1)).strftime(tfmt)
        return (start, end)

    request = context['request']
    abs_url = request.build_absolute_uri(action.get_absolute_url())
    title = urlquote_plus(action.html_title)
    desc = action_desc(action, abs_url)
    tzname = "America/New York"
    location = action_loc(action)

    if service == "Google":
        start, end = action_times(action, '%Y%m%dT%H%M')
        dates = urlquote_plus(f"{start}/{end}")
        ctz = urlquote_plus(tzname)
        url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&dates={dates}&ctz={ctz}&location={location}&text={title}&details={desc}"
        return mark_safe(url)
    elif service == "Yahoo":
        start, end = action_times(action, '%Y%m%dT%H%M00')
        return f"https://calendar.yahoo.com/?v=60&view=d&type=20&title={title}&st={start}&et={end}&desc={desc}&in_loc={location}&url={abs_url}"
    else:
        return f"/action/ics/{action.slug}"

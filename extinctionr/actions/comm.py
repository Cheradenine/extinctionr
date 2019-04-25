from django.conf import settings
from django.core.mail import send_mass_mail
from django.utils.timezone import now
from django.utils import dateformat

from .models import Action, Attendee


MESSAGE = '''
Hi {name},

You said you'd commit to attending "{action_name}" if at least {num} people also committed.
We've now got enough other folks to commit! We hope to see you there, on {action_date}.
More details here: {action_url}

Solidarity,
Extinction Rebellion Massachusetts

P.S. If you can't make it, please get in touch. We're all in this together.

'''


def notify_commitments(action, threshold, action_url):
	attendees = action.attendee_set.filter(mutual_commitment__lte=threshold)
	if attendees.count() >= threshold + 1:
		to_send = attendees.filter(notified=None, mutual_commitment__gt=0)
		subject = "[XR] We've got enough to commit to %s" % action.name
		messages = []
		modified = []
		from_email = settings.DEFAULT_FROM_EMAIL
		when = dateformat.format(action.when, 'l, F jS @ g:iA')
		for attendee in to_send:
			full_name = '%s %s' % (attendee.contact.first_name, attendee.contact.last_name)
			msg = MESSAGE.format(
				name=full_name,
				action_name=action.name,
				action_date=when,
				action_url=action_url,
				num=attendee.mutual_commitment,)
			messages.append((subject, msg, from_email, [attendee.contact.email]))
			attendee.notified = now()
			if not attendee.promised:
				attendee.promised = now()
			modified.append(attendee)
		send_mass_mail(messages)
		for attendee in modified:
			attendee.save()
		return len(messages)

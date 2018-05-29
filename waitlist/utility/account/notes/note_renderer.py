from waitlist.storage.database import AccountNote
from waitlist.utility.constants import account_notes
from waitlist.utility.eve_id_utils import get_character_by_id
import json
import logging


logger = logging.getLogger(__name__)


def render_note_text(note: AccountNote) -> str:
    if note.type == account_notes.TYPE_HUMAN:
        if note.note is None:
            return ''
        return note.note
    elif note.type == account_notes.TYPE_ACCOUNT_ACTIVE_CHANGED:
        if note.jsonPayload['new_disabled']:
            return "Account Disabled"
        else:
            return "Account Activated"

    elif note.type == account_notes.TYPE_ACCOUNT_CREATED:
        return f'Account created. Usernote: {note.note}'
    elif note.type == account_notes.TYPE_ACCOUNT_ROLES_CHANGED:
        if note.note is None:
            return ''
        return note.note
    elif note.type == account_notes.TYPE_GOT_ACCOUNT_MAIL:
        if note.jsonPayload['sender_character_id'] is None:
            sender = '<Unknown>'
        else:
            sender = get_character_by_id(
                note.jsonPayload['sender_character_id']).get_eve_name()

        if note.jsonPayload['target_character_id'] is None:
            target = '<Unknown>'
        else:
            target = get_character_by_id(
                note.jsonPayload['target_character_id']).get_eve_name()

        body = note.jsonPayload['mail_body']
        subject = note.jsonPayload['subject']
        if body is None:
            body = '<Unknown>'
        if subject is None:
            subject = '<Unknown>'

        return (f'Character {sender} sent mail to Character {target} which '
                f'was the active char of this account. '
                f'Mail Subject: {subject} Mail Body: {body}')
    elif note.type == account_notes.TYPE_ROLE_CREATED:
        return (f'Created Role with name={note.jsonPayload["role_name"]} '
                f'and display name={note.jsonPayload["display_name"]}')
    elif note.type == account_notes.TYPE_SENT_ACCOUNT_MAIL:

        character: Character = get_character_by_id(
            note.jsonPayload['sender_character_id'])
        recipientsJsonText = json.dumps(note.jsonPayload['recipients'])
        return (f'Account sent mail using character={character.eve_name} '
                f'to={recipientsJsonText} '
                f'with subject={note.jsonPayload["subject"]} '
                f'and body={note.jsonPayload["body"]}')
    elif note.type == account_notes.TYPE_ACCOUNT_NAME_CHANGED:
        return (f'Changed name from "{note.jsonPayload["old_name"]}" '
                f'to "{note.jsonPayload["new_name"]}"')
    else:
        logger.error('Unhandler AccountNote type: %s', note.type)
        return f'Unhandled AccountNote type: {note.type}'

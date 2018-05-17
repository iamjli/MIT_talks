"""
Shows basic usage of the Gmail API.

Lists the user's Gmail labels.
"""
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# Setup the Gmail API
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
store = file.Storage('../credentials/credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('../credentials/client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('gmail', 'v1', http=creds.authorize(Http()))

# Call the Gmail API
results = service.users().labels().list(userId='me').execute()
labels = results.get('labels', [])
if not labels:
    print('No labels found.')
else:
    print('Labels:')
    for label in labels:
        print(label['name'], label['id'])



from apiclient import errors
def ListMessagesWithLabels(service, user_id, label_ids=[]):
    """List all Messages of the user's mailbox with label_ids applied.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        label_ids: Only return Messages with these labelIds applied.

    Returns:
        List of Messages that have all required Labels applied. Note that the
        returned list contains Message IDs, you must use get with the
        appropriate id to get the details of a Message.
    """
    try:
        response = service.users().messages().list(userId=user_id, labelIds=label_ids, maxResults=10).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, labelIds=label_ids, pageToken=page_token, maxResults=10).execute()
            messages.extend(response['messages'])

        return messages
    except errors.HttpError:
        print('An error occurred: %s' % error)


tmp = ListMessagesWithLabels(service, 'me', 'Label_2744073883326323491')
print(tmp)
# ListMessagesWithLabels(service, 'me', 'Talks')
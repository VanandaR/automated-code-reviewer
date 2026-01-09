from jira import JIRA, JIRAError
from config import settings

class JiraService:
    def __init__(self):
        """Initializes the Jira Service and connects to the Jira server using Personal Access Token."""
        try:
            headers = {'Authorization': f'Bearer {settings.JIRA_PAT}'}
            options = {
                'server': settings.JIRA_SERVER,
                'headers': headers
            }
            # We pass token_auth=True to hint the library we are using a PAT
            self.client = JIRA(options, token_auth=settings.JIRA_PAT)
            print("Successfully connected to Jira using PAT.")
        except JIRAError as e:
            print(f"Failed to connect to Jira: {e.status_code}, {e.text}")
            raise

    def get_ticket_details(self, ticket_id):
        """
        Fetches details for a specific Jira ticket.
        Returns the issue object if found, otherwise None.
        """
        try:
            issue = self.client.issue(ticket_id)
            print(f"Successfully fetched details for ticket: {ticket_id}")
            return issue
        except JIRAError as e:
            if e.status_code == 404:
                print(f"Ticket {ticket_id} not found.")
            else:
                print(f"An error occurred while fetching ticket {ticket_id}: {e.text}")
            return None

    def post_comment(self, ticket_id, comment):
        """Posts a comment to a specific Jira ticket."""
        try:
            self.client.add_comment(ticket_id, comment)
            print(f"Successfully posted comment to ticket {ticket_id}.")
            return True
        except JIRAError as e:
            print(f"Failed to post comment to ticket {ticket_id}: {e.text}")
            return False

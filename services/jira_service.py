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

    def transition_ticket_status(self, ticket_id, transition_name):
        """Transitions a Jira ticket to a new status."""
        try:
            transitions = self.client.transitions(ticket_id)
            transition_id = None
            for t in transitions:
                if t['name'].lower() == transition_name.lower():
                    transition_id = t['id']
                    break
            
            if transition_id:
                self.client.transition_issue(ticket_id, transition_id)
                print(f"Successfully transitioned ticket {ticket_id} to '{transition_name}'.")
                return True
            else:
                print(f"Transition '{transition_name}' not found for ticket {ticket_id}.")
                available_transitions = [t['name'] for t in transitions]
                print(f"Available transitions: {available_transitions}")
                return False
        except JIRAError as e:
            print(f"Failed to transition ticket {ticket_id}: {e.text}")
            return False

    def find_cloned_issue(self, original_ticket_id):
        """Finds the issue that is a clone of the original ticket."""
        try:
            issue = self.client.issue(original_ticket_id, expand='issuelinks')
            for link in issue.fields.issuelinks:
                if hasattr(link, 'outwardIssue') and link.type.name == 'Cloners':
                    cloned_issue_key = link.outwardIssue.key
                    print(f"Found cloned issue: {cloned_issue_key}")
                    return self.client.issue(cloned_issue_key)
            print(f"No cloned issue found for ticket {original_ticket_id}.")
            return None
        except JIRAError as e:
            print(f"Error finding cloned issue for {original_ticket_id}: {e.text}")
            return None

    def update_issue_description(self, ticket_id, new_content):
        """Appends new content to a Jira ticket's description."""
        try:
            issue = self.client.issue(ticket_id)
            current_description = issue.fields.description or ""
            updated_description = current_description + "\n\n" + new_content
            issue.update(fields={'description': updated_description})
            print(f"Successfully updated description for ticket {ticket_id}.")
            return True
        except JIRAError as e:
            print(f"Failed to update description for ticket {ticket_id}: {e.text}")
            return False

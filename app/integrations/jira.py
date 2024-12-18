import os
import re
import requests
from typing import Optional
from models.chat import User

class JiraIntegration:
    def __init__(self):
        self.base_url = 'https://nextech.atlassian.net'

    def _make_request(self, method: str, endpoint: str, api_key: str, data: Optional[dict] = None) -> dict:
        """Make a request to the Jira API"""
        headers = {
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json"
        }
        url = f"{self.base_url}/rest/api/latest/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error making request to Jira API: {str(e)}")

    def parse_story_key(self, story: str) -> str:
        """
        Parse a story key from various formats:
        - XXX-1234
        - https://nextech.atlassian.net/browse/XXX-1234
        - git checkout -b XXX-1234-some-text
        """
        # Direct format (XXX-1234)
        if re.match(r'^[A-Z]{3}-\d{2,}$', story):
            return story
        
        # URL format
        url_match = re.search(r'https://nextech.atlassian.net/browse/([A-Z]{3}-\d{2,})', story)
        if url_match:
            return url_match.group(1)
        
        # Git branch format
        git_match = re.search(r'git checkout -b ([A-Z]{3}-\d{2,})', story)
        if git_match:
            return git_match.group(1)
        
        raise ValueError(
            "Invalid story format. Expected formats: "
            "XXX-1234, https://nextech.atlassian.net/browse/XXX-1234, "
            "or git checkout -b XXX-1234-story-summary"
        )

    def get_story_details(self, story_key: str, user: User) -> dict:
        """Get the details of a Jira story"""
        story_key = self.parse_story_key(story_key)
        api_key = user.get_api_key('jira')
        return self._make_request('GET', f'issue/{story_key}', api_key)

    def get_story_description(self, story_key: str, user: User) -> str:
        """Get just the description of a Jira story"""
        story_details = self.get_story_details(story_key, user)
        return story_details.get('fields', {}).get('description', '')

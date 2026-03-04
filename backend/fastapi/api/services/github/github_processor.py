from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# NLTK Setup for Sentiment Analysis
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    try:
        nltk.download('vader_lexicon', quiet=True)
    except Exception as e:
        print(f"[WARN] NLTK Download Failed: {e}")


class GitHubProcessor:
    """Handles data processing and transformation of GitHub API responses."""

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo
        self.sia = SentimentIntensityAnalyzer()

    def process_pulse_feed(self, events: List[Dict[str, Any]], limit: int = 15) -> List[Dict[str, Any]]:
        """Process raw GitHub events into formatted pulse feed items."""
        if not events:
            return []

        processed_events = []
        for event in events[:limit]:
            processed_event = self._process_single_event(event)
            if processed_event:
                processed_events.append(processed_event)

        return processed_events

    def _process_single_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single GitHub event."""
        event_type = event.get('type')
        payload = event.get('payload', {})
        repo = event.get('repo', {})
        actor = event.get('actor', {})

        if event_type == 'PushEvent':
            count = len(payload.get('commits', []))
            ref = payload.get('ref', '').split('/')[-1]
            action = f"pushed {count} commit{'s' if count != 1 else ''} to {ref}"
        elif event_type == 'PullRequestEvent':
            action = payload.get('action', 'interacted with')
            pr = payload.get('pull_request', {})
            action = f"{action} pull request #{pr.get('number')}"
        elif event_type == 'IssuesEvent':
            action = payload.get('action', 'interacted with')
            issue = payload.get('issue', {})
            action = f"{action} issue #{issue.get('number')}"
        elif event_type == 'IssueCommentEvent':
            action = "commented on issue"
            issue = payload.get('issue', {})
            if issue:
                action = f"{action} #{issue.get('number')}"
        elif event_type == 'PullRequestReviewCommentEvent':
            action = "reviewed pull request"
            pr = payload.get('pull_request', {})
            if pr:
                action = f"{action} #{pr.get('number')}"
        elif event_type == 'CreateEvent':
            ref_type = payload.get('ref_type')
            ref = payload.get('ref')
            action = f"created {ref_type} {ref or ''}"
        elif event_type == 'DeleteEvent':
            ref_type = payload.get('ref_type')
            ref = payload.get('ref')
            action = f"deleted {ref_type} {ref or ''}"
        elif event_type == 'ForkEvent':
            action = "forked the repository"
        elif event_type == 'WatchEvent':
            action = "starred the repository"
        else:
            return None

        return {
            "id": event.get('id'),
            "type": event_type,
            "actor": {
                "login": actor.get('login'),
                "avatar": actor.get('avatar_url')
            },
            "repo": {
                "name": repo.get('name'),
                "url": f"https://github.com/{repo.get('name')}"
            },
            "action": action,
            "created_at": event.get('created_at')
        }

    def process_repo_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process repository data into stats format."""
        if not data:
            return {}

        return {
            "name": data.get('name'),
            "full_name": data.get('full_name'),
            "description": data.get('description'),
            "stars": data.get('stargazers_count', 0),
            "forks": data.get('forks_count', 0),
            "watchers": data.get('watchers_count', 0),
            "language": data.get('language'),
            "created_at": data.get('created_at'),
            "updated_at": data.get('updated_at'),
            "size": data.get('size'),
            "open_issues": data.get('open_issues_count', 0)
        }

    def process_recent_prs(self, prs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process pull requests data."""
        if not prs:
            return []

        processed_prs = []
        for pr in prs:
            processed_prs.append({
                "number": pr.get('number'),
                "title": pr.get('title'),
                "state": pr.get('state'),
                "created_at": pr.get('created_at'),
                "updated_at": pr.get('updated_at'),
                "merged_at": pr.get('merged_at'),
                "user": {
                    "login": pr.get('user', {}).get('login'),
                    "avatar": pr.get('user', {}).get('avatar_url')
                },
                "labels": [label.get('name') for label in pr.get('labels', [])]
            })
        return processed_prs

    def process_contributors(self, contributors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process contributors data."""
        if not contributors:
            return []

        processed_contributors = []
        for contributor in contributors:
            processed_contributors.append({
                "login": contributor.get('login'),
                "avatar": contributor.get('avatar_url'),
                "contributions": contributor.get("contributions"),
                "type": contributor.get('type')
            })
        return processed_contributors

    def process_activity(self, activity_data: List[Dict[str, Any]], commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process commit activity data with fallback to manual aggregation."""
        if activity_data and len(activity_data) > 0:
            return [
                {
                    "week": item.get('week'),
                    "total": item.get('total'),
                    "days": item.get('days', [])
                }
                for item in activity_data
            ]
        elif commits:
            activity_map = {}
            for c in commits:
                if not c.get('commit', {}).get('author', {}).get('date'):
                    continue
                date_str = c['commit']['author']['date']
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    week_start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    week_start = week_start - timedelta(days=dt.weekday())
                    week_key = int(week_start.timestamp())

                    if week_key not in activity_map:
                        activity_map[week_key] = {"week": week_key, "total": 0, "days": [0] * 7}

                    day_index = dt.weekday()
                    activity_map[week_key]["days"][day_index] += 1
                    activity_map[week_key]["total"] += 1
                except Exception:
                    continue

            return list(activity_map.values())
        return []

    def calculate_total_commits(self, contributors: List[Dict[str, Any]]) -> int:
        """Calculate total commits from contributors data."""
        if not contributors:
            return 0
        return sum(c.get('contributions', 0) for c in contributors)

    def process_contribution_mix(self, total_commits: int, total_prs: int, total_issues: int, total_reviews: int) -> List[Dict[str, Any]]:
        """Process contribution statistics into mix format."""
        return [
            {
                "name": "Core Features",
                "value": 45,
                "count": total_commits,
                "unit": "Commits",
                "color": "#3B82F6",
                "description": "Functional code changes & features"
            },
            {
                "name": "Infrastructure",
                "value": 25,
                "count": total_prs,
                "unit": "Pull Requests",
                "color": "#10B981",
                "description": "PR merges and branch management"
            },
            {
                "name": "Issue Triage",
                "value": 20,
                "count": total_issues,
                "unit": "Total Issues",
                "color": "#C2410C",
                "description": "Issue resolution & bug tracking"
            },
            {
                "name": "Mentorship",
                "value": 10,
                "count": total_reviews,
                "unit": "Review Comments",
                "color": "#8B5CF6",
                "description": "Peer code reviews & guidance"
            },
        ]

    def process_reviewer_stats(self, comments: List[Dict[str, Any]], reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process reviewer statistics with sentiment analysis."""
        reviewers = {}
        total_sentiment = 0.0
        details_count = 0

        BOTS = {"copilot", "github-copilot", "github-copilot[bot]", "actions-user", "github-actions[bot]"}

        def process_entry(entry: Dict[str, Any], is_review: bool = False):
            nonlocal total_sentiment, details_count
            user = entry.get('user', {}).get('login')
            if not user or '[bot]' in user.lower() or user.endswith('-bot') or user.lower() in BOTS:
                return

            if user not in reviewers:
                reviewers[user] = {
                    "name": user,
                    "avatar": entry.get('user', {}).get('avatar_url'),
                    "count": 0,
                    "is_maintainer": user == self.owner
                }
            reviewers[user]["count"] += 1

            body = entry.get('body', '')
            if body and len(body.strip()) > 3:
                try:
                    score = self.sia.polarity_scores(body)['compound']
                    total_sentiment += score
                    details_count += 1
                except Exception:
                    pass

        for comment in comments:
            process_entry(comment, is_review=False)
        for review in reviews:
            process_entry(review, is_review=True)

        avg_sentiment = total_sentiment / details_count if details_count > 0 else 0

        return {
            "reviewers": list(reviewers.values()),
            "total_reviews": len(reviews),
            "total_comments": len(comments),
            "sentiment_score": avg_sentiment,
            "sentiment_label": "Positive" if avg_sentiment >= 0.05 else "Negative" if avg_sentiment <= -0.05 else "Neutral"
        }
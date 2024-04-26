import pytest
from unittest.mock import patch, MagicMock
from cloudron_utils.cloudron_notifications import get_cloudron_notifications, mark_notification_as_acknowledged

@patch('requests.get')
def test_get_cloudron_notifications(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"id": "1", "message": "Test notification 1", "acknowledged": False},
        {"id": "2", "message": "Test notification 2", "acknowledged": True}
    ]
    mock_get.return_value = mock_response

    notifications = get_cloudron_notifications()

    assert len(notifications) == 2
    assert notifications[0]['id'] == "1"
    assert notifications[0]['message'] == "Test notification 1"
    assert notifications[0]['acknowledged'] == False


@patch('requests.post')
def test_mark_notification_as_acknowledged(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    mark_notification_as_acknowledged("1")

    mock_post.assert_called_once_with(
        "https://domain/api/v1/notifications/1",
        headers={'Authorization': 'Bearer token'},
        json={"acknowledged": True}
    )
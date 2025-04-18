function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function sendFriendRequest(userId, button) {
    const csrftoken = getCookie('csrftoken');
    const errorDiv = button.nextElementSibling;
    
    try {
        const response = await fetch(`/send-request/${userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        if (response.ok) {
            // Update all instances of this user's friend button on the page
            updateAllUserButtons(userId, 'request-sent');
        } else {
            const data = await response.json();
            showError(button, data.error || 'Failed to send friend request');
        }
    } catch (error) {
        showError(button, 'Network error occurred');
    }
}

async function cancelFriendRequest(userId, button) {
    const csrftoken = getCookie('csrftoken');
    
    try {
        const response = await fetch(`/cancel-request/${userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        if (response.ok) {
            updateAllUserButtons(userId, 'add');
        } else {
            const data = await response.json();
            showError(button, data.error || 'Failed to cancel request');
        }
    } catch (error) {
        showError(button, 'Network error occurred');
    }
}

async function acceptFriendRequest(requestId, userId, button) {
    const csrftoken = getCookie('csrftoken');
    
    try {
        const response = await fetch(`/accept-request/${requestId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        if (response.ok) {
            updateAllUserButtons(userId, 'friends');
        } else {
            const data = await response.json();
            showError(button, data.error || 'Failed to accept request');
        }
    } catch (error) {
        showError(button, 'Network error occurred');
    }
}

async function removeFriend(userId, button) {
    if (!confirm('Are you sure you want to remove this friend?')) {
        return;
    }

    const csrftoken = getCookie('csrftoken');
    
    try {
        const response = await fetch(`/remove-friend/${userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        if (response.ok) {
            updateAllUserButtons(userId, 'add');
            // If on friends list page, optionally remove the entire friend card
            const friendCard = button.closest('.friend-card');
            if (friendCard) {
                friendCard.remove();
            }
        } else {
            const data = await response.json();
            showError(button, data.error || 'Failed to remove friend');
        }
    } catch (error) {
        showError(button, 'Network error occurred');
    }
}

function updateAllUserButtons(userId, state) {
    // Find all buttons related to this user
    const userCards = document.querySelectorAll(`[data-user-id="${userId}"]`);
    
    userCards.forEach(card => {
        const button = card.querySelector('.action-btn');
        const errorDiv = card.querySelector('.error-message');
        
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }

        switch (state) {
            case 'request-sent':
                button.className = 'action-btn pending-btn';
                button.textContent = '📨 Request Sent';
                button.disabled = true;
                break;
            case 'friends':
                button.className = 'action-btn pending-btn';
                button.textContent = '✓ Friends';
                button.disabled = true;
                break;
            case 'add':
                button.className = 'action-btn add-btn';
                button.textContent = 'Add Friend';
                button.disabled = false;
                button.onclick = () => sendFriendRequest(userId, button);
                break;
        }
    });
}

function showError(button, message) {
    const errorDiv = button.nextElementSibling;
    if (errorDiv && errorDiv.classList.contains('error-message')) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
} 
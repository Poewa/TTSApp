def test_home_page_redirects(client):
    """Test that home page redirects to login if auth is required"""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Log ind' in response.data or b'Login' in response.data

def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Brugernavn' in response.data


import { UserManager, WebStorageStateStore } from 'oidc-client-ts';

(function () {
    'use strict';

    const COGNITO_DOMAIN =
        'https://ap-southeast-2dnfvhpo71.auth.ap-southeast-2.amazoncognito.com';

    const CLIENT_ID = '19n3uoseoiq5sjmhqc0eu6q3dv';
    const REDIRECT_URI = window.location.origin;

    const userManager = new UserManager({
        authority:
            'https://cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_DnFvHpO71',
        client_id: CLIENT_ID,
        redirect_uri: REDIRECT_URI,
        response_type: 'code',
        scope: 'openid email phone',
        userStore: new WebStorageStateStore({
            store: window.sessionStorage
        })
    });

    const loginButton = document.getElementById('login-button');
    const logoutButton = document.getElementById('logout-button');
    const userInfo = document.getElementById('user-info');
    const userEmail = document.getElementById('user-email');

    function showSignedOut() {
        loginButton.hidden = false;
        userInfo.hidden = true;
    }

    function showSignedIn(user) {
        loginButton.hidden = true;
        userInfo.hidden = false;
        userEmail.textContent =
            user.profile.email || user.profile.name || 'Signed in';
    }

    async function initializeAuth() {
        try {
            let user;

            if (
                window.location.search.includes('code=') ||
                window.location.search.includes('error=')
            ) {
                user = await userManager.signinCallback();

                window.history.replaceState(
                    {},
                    document.title,
                    window.location.pathname
                );
            } else {
                user = await userManager.getUser();
            }

            if (user && !user.expired) {
                showSignedIn(user);
            } else {
                showSignedOut();
            }
        } catch (error) {
            console.error('Sign-in initialization failed:', error);
            showSignedOut();
        }
    }

    loginButton.addEventListener('click', async () => {
        try {
            await userManager.signinRedirect();
        } catch (error) {
            console.error('Google sign-in failed:', error);
            alert('Unable to start sign-in. Please try again.');
        }
    });

    logoutButton.addEventListener('click', async () => {
        try {
            await userManager.removeUser();

            const logoutURL =
                `${COGNITO_DOMAIN}/logout` +
                `?client_id=${CLIENT_ID}` +
                `&logout_uri=${encodeURIComponent(REDIRECT_URI)}`;

            window.location.assign(logoutURL);
        } catch (error) {
            console.error('Sign-out failed:', error);
            alert('Unable to sign out. Please try again.');
        }
    });

    initializeAuth();
})();

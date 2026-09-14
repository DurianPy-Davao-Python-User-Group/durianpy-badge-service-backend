"""AWS Cognito access token verifier adapter validating JWT signatures and claims."""

from typing import Any, Optional

import jwt

from src.application.ports.security.token_verifier_port import TokenVerifierPort
from src.core.logging import logger, mask_string
from src.core.settings import settings
from src.domain.exceptions.auth_exceptions import AuthenticationError
from src.domain.models.authenticated_user import AuthenticatedUser


class CognitoTokenVerifier(TokenVerifierPort):
    """Infrastructure adapter verifying Cognito access tokens against JWKS."""

    def __init__(
        self,
        jwks_url: Optional[str] = None,
        issuer: Optional[str] = None,
        user_pool_id: Optional[str] = None,
        app_client_id: Optional[str] = None,
        jwks_client: Optional[jwt.PyJWKClient] = None,
    ) -> None:
        """
        Initialize the Cognito token verifier.

        :param jwks_url: Optional JWKS endpoint URL, defaults to settings.cognito_jwks_url.
        :type jwks_url: Optional[str]
        :param issuer: Optional expected token issuer URL, defaults to settings.cognito_issuer.
        :type issuer: Optional[str]
        :param user_pool_id: Optional Cognito user pool ID, defaults to settings.COGNITO_USER_POOL_ID.
        :type user_pool_id: Optional[str]
        :param app_client_id: Optional expected Cognito app client ID, defaults to settings.COGNITO_APP_CLIENT_ID.
        :type app_client_id: Optional[str]
        :param jwks_client: Optional custom or mock PyJWKClient instance.
        :type jwks_client: Optional[jwt.PyJWKClient]
        """
        self.__user_pool_id = user_pool_id if user_pool_id is not None else settings.COGNITO_USER_POOL_ID
        self.__app_client_id = app_client_id if app_client_id is not None else settings.COGNITO_APP_CLIENT_ID
        self.__issuer = issuer if issuer is not None else settings.cognito_issuer

        if jwks_client is not None:
            self.__jwks_client = jwks_client
        else:
            resolved_jwks_url = (
                jwks_url if jwks_url is not None else (settings.cognito_jwks_url if self.__user_pool_id else None)
            )
            if resolved_jwks_url:
                self.__jwks_client = jwt.PyJWKClient(resolved_jwks_url, cache_keys=True, max_cached_keys=16)
            else:
                self.__jwks_client = None

    def verify(self, token: str) -> AuthenticatedUser:
        """
        Decode and verify a Cognito Bearer access token.

        Validates RS256 signature against cached JWKS keys, confirms token expiration,
        ensures token_use is 'access', and matches the configured client ID and issuer.

        :param token: Raw Bearer access token string.
        :type token: str
        :returns: Verified authenticated user domain model.
        :rtype: AuthenticatedUser
        :raises AuthenticationError: If the token is expired, invalid, or has unauthorized claims.
        """
        if not token or not isinstance(token, str):
            raise AuthenticationError('Authentication token must be a non-empty string.')

        if self.__jwks_client is None:
            logger.error('Cognito JWKS client is unconfigured. Missing COGNITO_USER_POOL_ID setting.')
            raise AuthenticationError('Authentication service is temporarily misconfigured.')

        signing_key = self.__get_signing_key(token)
        payload = self.__decode_and_validate_payload(token, signing_key)
        return self.__extract_user(payload)

    def __get_signing_key(self, token: str) -> jwt.PyJWK:
        """
        Retrieve the RSA signing key matching the token's key ID from JWKS.

        :param token: Raw Bearer access token string.
        :type token: str
        :returns: PyJWK signing key instance.
        :rtype: jwt.PyJWK
        :raises AuthenticationError: If key retrieval fails or token headers are malformed.
        """
        try:
            return self.__jwks_client.get_signing_key_from_jwt(token)
        except jwt.PyJWKClientError as exc:
            logger.warning(f'Failed to retrieve signing key from JWKS: {exc}')
            raise AuthenticationError('Unable to verify token signature against identity provider JWKS.') from exc
        except jwt.PyJWTError as exc:
            logger.warning(f'Invalid token header structure: {exc}')
            raise AuthenticationError('Invalid token format or header.') from exc

    def __decode_and_validate_payload(self, token: str, signing_key: jwt.PyJWK) -> dict[str, Any]:
        """
        Decode JWT payload and verify cryptographic signature and standard claims.

        :param token: Raw Bearer access token string.
        :type token: str
        :param signing_key: Signing key matching the token header.
        :type signing_key: jwt.PyJWK
        :returns: Decoded JWT claims dictionary.
        :rtype: dict[str, Any]
        :raises AuthenticationError: If token signature, expiry, or issuer validation fails.
        """
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                issuer=self.__issuer if self.__user_pool_id else None,
                options={
                    'verify_aud': False,
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'verify_nbf': True,
                },
            )
        except jwt.ExpiredSignatureError as exc:
            logger.warning('Provided access token has expired.')
            raise AuthenticationError('Token has expired.') from exc
        except jwt.InvalidIssuerError as exc:
            logger.warning(f'Token issuer mismatch: {exc}')
            raise AuthenticationError('Token was not issued by the configured identity provider.') from exc
        except jwt.InvalidSignatureError as exc:
            logger.warning('Token signature verification failed.')
            raise AuthenticationError('Invalid token signature.') from exc
        except jwt.PyJWTError as exc:
            logger.warning(f'Token decoding failure: {exc}')
            raise AuthenticationError('Invalid or corrupted authentication token.') from exc

        token_use = payload.get('token_use')
        if token_use != 'access':
            logger.warning(f"Invalid token_use '{token_use}': expected 'access'.")
            raise AuthenticationError("Invalid token use: expected an 'access' token.")

        if self.__app_client_id:
            token_client_id = payload.get('client_id')
            if token_client_id != self.__app_client_id:
                logger.warning(f"Token client_id '{token_client_id}' does not match configured app client.")
                raise AuthenticationError('Token was not issued for this client application.')

        return payload

    def __extract_user(self, payload: dict[str, Any]) -> AuthenticatedUser:
        """
        Extract authenticated user domain model from validated claims payload.

        :param payload: Validated JWT claims dictionary.
        :type payload: dict[str, Any]
        :returns: Authenticated user domain model.
        :rtype: AuthenticatedUser
        :raises AuthenticationError: If required subject identifier is missing.
        """
        user_id = payload.get('sub')
        if not user_id:
            logger.warning("Token missing required 'sub' claim.")
            raise AuthenticationError('Token is missing required subject identifier.')

        username = payload.get('username') or user_id
        raw_groups = payload.get('cognito:groups', [])
        groups = list(raw_groups) if isinstance(raw_groups, (list, tuple)) else []

        raw_scope = payload.get('scope', '')
        scopes = raw_scope.split() if isinstance(raw_scope, str) else []

        client_id = payload.get('client_id')

        user = AuthenticatedUser(
            user_id=str(user_id),
            username=str(username),
            groups=groups,
            scopes=scopes,
            client_id=client_id,
            raw_claims=payload,
        )

        logger.info(
            f"Authenticated user '{mask_string(user.user_id)}' (username '{mask_string(user.username)}') "
            f'with groups {user.groups} and scopes {user.scopes}'
        )
        return user

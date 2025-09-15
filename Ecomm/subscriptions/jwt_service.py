import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import UserSubscription
import hashlib
import logging
import os

logger = logging.getLogger(__name__)

# Get the User model dynamically
User = get_user_model()

class JWTSubscriptionService:
    
    # Token expiration times
    ADMIN_TOKEN_EXPIRY = timedelta(days=30)
    USER_TOKEN_BUFFER = timedelta(hours=1)  # Buffer before subscription expiry
    
    @staticmethod
    def _get_jwt_secret():
        """Get JWT secret key from settings with fallback to environment"""
        # Try to get from environment first for security
        secret = os.getenv('JWT_SECRET_KEY')
        if not secret:
            # Fallback to settings
            secret = getattr(settings, 'JWT_SECRET_KEY', None)
        
        if not secret:
            # Use Django's SECRET_KEY as last resort
            secret = settings.SECRET_KEY
            logger.warning("Using Django SECRET_KEY for JWT. Consider setting JWT_SECRET_KEY.")
        
        return secret
    
    @staticmethod
    def _create_token_hash(user_id, subscription_id=None):
        """Create a hash for token blacklisting"""
        data = f"{user_id}_{subscription_id or 'admin'}_{timezone.now().date()}"
        return hashlib.md5(data.encode()).hexdigest()
    
    @staticmethod
    def generate_subscription_token(user, subscription):
        """Generate JWT token with subscription claims"""
        
        if not subscription.is_valid:
            raise ValueError("Cannot generate token for invalid subscription")
        
        # Determine role based on plan type and user status
        if user.is_superuser or user.is_staff:
            role = 'admin'
        elif subscription.plan.plan_type == 'researcher':
            role = 'researcher'
        elif subscription.plan.plan_type == 'premium':
            role = 'premium_user'
        else:
            role = 'user'
        
        # Calculate token expiry (subscription end or buffer time, whichever is sooner)
        token_expiry = min(
            subscription.end_date,
            timezone.now() + JWTSubscriptionService.ADMIN_TOKEN_EXPIRY
        )
        
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role': role,
            'subscription_id': subscription.id,
            'plan_type': subscription.plan.plan_type,
            'plan_name': subscription.plan.name,
            'rate_limit': subscription.plan.api_rate_limit,
            'features': subscription.plan.features,
            'subscription_end': subscription.end_date.isoformat(),
            'days_remaining': subscription.days_remaining,
            'iat': timezone.now(),
            'exp': token_expiry,
            'subscription_active': True,
            'auto_renew': subscription.auto_renew,
            'jti': JWTSubscriptionService._create_token_hash(user.id, subscription.id)
        }
        
        try:
            token = jwt.encode(payload, JWTSubscriptionService._get_jwt_secret(), algorithm='HS256')
            logger.info(f"Generated subscription token for user {user.username}")
            return token
        except Exception as e:
            logger.error(f"Failed to generate subscription token: {str(e)}")
            raise
    
    @staticmethod
    def generate_admin_token(user):
        """Generate JWT token for admin users"""
        if not (user.is_superuser or user.is_staff):
            raise ValueError("User is not an admin")
        
        expiry_time = timezone.now() + JWTSubscriptionService.ADMIN_TOKEN_EXPIRY
        
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role': 'admin',
            'plan_type': 'admin',
            'plan_name': 'Administrator',
            'rate_limit': 10000,  # High rate limit for admins
            'features': ['unlimited_api', 'admin_panel', 'user_management'],
            'iat': timezone.now(),
            'exp': expiry_time,
            'subscription_active': True,
            'is_admin': True,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'jti': JWTSubscriptionService._create_token_hash(user.id)
        }
        
        try:
            token = jwt.encode(payload, JWTSubscriptionService._get_jwt_secret(), algorithm='HS256')
            logger.info(f"Generated admin token for user {user.username}")
            return token
        except Exception as e:
            logger.error(f"Failed to generate admin token: {str(e)}")
            raise
    
    @staticmethod
    def verify_token(token):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                JWTSubscriptionService._get_jwt_secret(), 
                algorithms=['HS256']
            )
            
            # Check if token is blacklisted
            jti = payload.get('jti')
            if jti and cache.get(f"blacklisted_token_{jti}"):
                logger.warning(f"Attempted use of blacklisted token: {jti}")
                return None
            
            # For non-admin tokens, verify subscription is still valid
            if not payload.get('is_admin') and payload.get('subscription_id'):
                try:
                    subscription = UserSubscription.objects.get(id=payload['subscription_id'])
                    if not subscription.is_valid:
                        logger.warning(f"Token verification failed: Invalid subscription {subscription.id}")
                        return None
                    
                    # Update payload with current subscription data
                    payload['subscription_active'] = True
                    payload['days_remaining'] = subscription.days_remaining
                    
                except UserSubscription.DoesNotExist:
                    logger.warning(f"Token verification failed: Subscription {payload['subscription_id']} not found")
                    return None
            
            logger.debug(f"Successfully verified token for user {payload.get('username')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token verification failed: Invalid token - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {str(e)}")
            return None
    
    @staticmethod
    def blacklist_token(token):
        """Blacklist a token (for logout functionality)"""
        try:
            payload = jwt.decode(
                token, 
                JWTSubscriptionService._get_jwt_secret(), 
                algorithms=['HS256'],
                options={"verify_exp": False}  # Don't verify expiration for blacklisting
            )
            
            jti = payload.get('jti')
            if jti:
                # Calculate remaining time until token expiry
                exp_timestamp = payload.get('exp')
                if isinstance(exp_timestamp, datetime):
                    remaining_time = exp_timestamp - timezone.now()
                else:
                    remaining_time = datetime.fromtimestamp(exp_timestamp) - datetime.utcnow()
                
                # Only blacklist if token hasn't expired yet
                if remaining_time.total_seconds() > 0:
                    cache.set(
                        f"blacklisted_token_{jti}", 
                        True, 
                        timeout=int(remaining_time.total_seconds())
                    )
                    logger.info(f"Token blacklisted: {jti}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to blacklist token: {str(e)}")
            return False
    
    @staticmethod
    def refresh_token(token):
        """Refresh a token if it's close to expiry"""
        try:
            payload = JWTSubscriptionService.verify_token(token)
            if not payload:
                return None
            
            # Check if token is close to expiry (within 1 day)
            exp_timestamp = payload.get('exp')
            if isinstance(exp_timestamp, str):
                exp_time = datetime.fromisoformat(exp_timestamp.replace('Z', '+00:00'))
            else:
                exp_time = datetime.fromtimestamp(exp_timestamp)
            
            time_until_expiry = exp_time - datetime.utcnow()
            
            if time_until_expiry.days <= 1:
                # Generate new token
                user = User.objects.get(id=payload['user_id'])
                
                if payload.get('is_admin'):
                    return JWTSubscriptionService.generate_admin_token(user)
                else:
                    subscription = UserSubscription.objects.get(id=payload['subscription_id'])
                    return JWTSubscriptionService.generate_subscription_token(user, subscription)
            
            return token  # Token doesn't need refresh yet
            
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            return None
    
    @staticmethod
    def get_user_permissions(token):
        """Extract user permissions from token"""
        payload = JWTSubscriptionService.verify_token(token)
        if not payload:
            return None
        
        permissions = {
            'can_access_api': payload.get('subscription_active', False),
            'rate_limit': payload.get('rate_limit', 0),
            'features': payload.get('features', []),
            'role': payload.get('role', 'user'),
            'is_admin': payload.get('is_admin', False),
            'plan_type': payload.get('plan_type'),
            'days_remaining': payload.get('days_remaining', 0)
        }
        
        return permissions
    
    @staticmethod
    def create_flask_response(payload):
        """Create Flask-compatible response format"""
        if not payload:
            return {
                'valid': False,
                'error': 'Invalid or expired token'
            }
        
        return {
            'valid': True,
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'email': payload.get('email'),
            'role': payload.get('role'),
            'plan_type': payload.get('plan_type'),
            'plan_name': payload.get('plan_name'),
            'rate_limit': payload.get('rate_limit'),
            'features': payload.get('features', []),
            'subscription_active': payload.get('subscription_active', False),
            'expires_at': payload.get('exp'),
            'days_remaining': payload.get('days_remaining', 0)
        }
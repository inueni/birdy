from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth1Session, OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.common import to_unicode
import requests
import json

TWITTER_API_VERSION = '1.1'
TWITTER_BASE_API_URL = 'https://api.twitter.com'


class TwitterClientError(Exception):
    pass


class TwitterApiError(Exception):
    def __init__(self, msg, error_code=None, status_code=None, headers=None):
        self.error_code = error_code
        self.status_code = status_code
        self.headers = headers
        super(TwitterApiError, self).__init__(msg)
        

class TwitterRateLimitError(TwitterApiError):
    pass


class TwitterAuthError(TwitterApiError):
    pass


class ApiComponent(object):
    def __init__(self, client, path=None):
        self._client = client
        self._path = path
    
    def __repr__(self):
        return '<ApiComponent: %s>' % self._path
    
    def __getitem__(self, path):
        if not self._path is None:
            path = '%s/%s' % (self._path, path)
        return ApiComponent(self._client, path)
    
    def __getattr__(self, path):
        return self[path]
    
    def get(self, **params):
        if self._path is None:
            raise TwitterClientError('Calling get() on an empty API path is not supported.')
        return self._client.request('GET', self._path, **params)
        
    def post(self, **params):
        if self._path is None:
            raise TwitterClientError('Calling post() on an empty API path is not supported.')
        return self._client.request('POST', self._path, **params)

    def get_path(self):
        return self._path
    

class ApiResponse(object):
    def __init__(self, resource_url, status_code, data, headers):
        self.resource_url = resource_url
        self.data = data
        self.headers = headers
        self.status_code = status_code


class TwitterObject(dict):
    def __getattr__(self, name):
        if name in self.iterkeys():
            return self[name]
        raise AttributeError('%s has no property named %s.' % (self.__class__.__name__, name))
    
    def __setattr__(self, *args):
        raise AttributeError('%s instances are read-only.' % self.__class__.__name__)
    __delattr__ = __setitem__ = __delitem__ = __setattr__
    
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, dict.__repr__(self))


class TwitterClientMixin(object):
    def request(self, method, path, **params):
        method = method.upper()
        url = '%s/%s/%s.json' % (self.base_api_url, self.api_version, path)
        request_kwargs = {}
        params, files = self.sanitize_params(params)
        
        if method == 'GET':
            request_kwargs['params'] = params
        elif method == 'POST':
            request_kwargs['data'] = params
            request_kwargs['files'] = files
        
        try:
            response = self.session.request(method, url, **request_kwargs)
        except requests.RequestException as e:
            raise TwitterClientError(str(e))
        
        try:
            data = response.json(object_hook=self.get_json_object_hook)
        except ValueError:
            data = None
        
        if response.status_code > 304:
            error_code, error_msg = self.get_twitter_error_details(data)
            endpoint = '%s %s' % (method, response.url)
            error_msg = '%s at %s.' % (error_msg, endpoint)
            
            if response.status_code == 404:
                raise TwitterApiError('Invalid API resource at %s.' % endpoint,
                                      error_code, response.status_code)
            
            elif response.status_code == 429:
                raise TwitterRateLimitError(error_msg, error_code, response.status_code, response.headers)
            
            elif response.status_code == 401 or 'Bad Authentication data' in error_msg:
                raise TwitterAuthError(error_msg, error_code, response.status_code)
            
            else:
                raise TwitterApiError(error_msg, error_code, response.status_code)
        
        if data is None and not response.status_code in (200, 201, 202):
            raise TwitterApiError('Response was not valid JSON, unable to decode at %s.' % endpoint,
                                  None, response.status_code)
        
        return ApiResponse(resource_url=response.url,
                           status_code=response.status_code,
                           data=data,
                           headers=response.headers)
    
    @staticmethod
    def sanitize_params(input_params):
        params, files = ({}, {})
        
        for k, v in input_params.items():
            if hasattr(v, 'read') and callable(v.read):
                files[k] = v
            elif isinstance(v, bool):
                if v:
                    params[k] = 'true'
                else:
                    params[k] = 'false'
            elif isinstance(v, list):
                params[k] = ','.join(v)
            else:
                params[k] = v
        return params, files    
    
    @staticmethod
    def get_json_object_hook(data):
        return TwitterObject(data)
    
    @staticmethod
    def get_twitter_error_details(data):
        code, msg = (None, 'An unknown error has occured processing your request.')
        errors = data.get('errors') if data else None
        
        if errors and isinstance(errors, list):
            code = errors[0]['code']
            msg = errors[0]['message']
        elif errors:
            code = errors['code']
            msg = errors['message']
        
        return (code, msg)


class UserClient(TwitterClientMixin):
    def __init__(self, consumer_key, consumer_secret, access_token=None, access_token_secret=None,
                 api_version=TWITTER_API_VERSION, base_api_url=TWITTER_BASE_API_URL):
        
        self.api_version = api_version
        self.base_api_url = base_api_url
        
        self.request_token_url = '%s/oauth/request_token' % self.base_api_url
        self.access_token_url = '%s/oauth/access_token' % self.base_api_url
        self.base_signin_url = '%s/oauth/authenticate' % self.base_api_url
        self.base_authorize_url = '%s/oauth/authorize' % self.base_api_url
        
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        
        self.session = self.get_oauth_session()
        
        self.api = ApiComponent(self)
    
    def get_oauth_session(self, ):
        return OAuth1Session(client_key=self.consumer_key,
                             client_secret=self.consumer_secret,
                             resource_owner_key=self.access_token,
                             resource_owner_secret=self.access_token_secret)
    
    def get_signin_token(self, callback_url=None, auto_set_token=True, **kwargs):
        return self.get_request_token(self.base_signin_url, callback_url, auto_set_token, **kwargs)
    
    def get_authorize_token(self, callback_url=None, auto_set_token=True, **kwargs):
        return self.get_request_token(self.base_authorize_url, callback_url, auto_set_token, **kwargs)
    
    def get_request_token(self, base_auth_url=None, callback_url=None, auto_set_token=True, **kwargs):
        if callback_url:
            self.session._client.client.callback_uri = to_unicode(callback_url, 'utf-8')
            
        try:
            token = self.session.fetch_request_token(self.request_token_url)
        except requests.RequestException as e:
            raise TwitterClientError(str(e))
        except ValueError as e:
            raise TwitterClientError('Response does not contain a token.')
        
        if base_auth_url:
            token['auth_url'] = self.session.authorization_url(base_auth_url, **kwargs)
        
        if auto_set_token:
            self.auto_set_token(token)
        
        return TwitterObject(token)
    
    def get_access_token(self, oauth_verifier, auto_set_token=True):
        required = (self.access_token, self.access_token_secret)
        
        if not all(required):
            raise TwitterClientError('%s must be initialized with access_token and access_token_secret to fetch authorized access token.')
        
        self.session._client.client.verifier = to_unicode(oauth_verifier, 'utf-8')
        
        try:
            token = self.session.fetch_access_token(self.access_token_url)
        except request.RequestException as e:
            raise TwitterClientError(str(e))
        except ValueError:
            raise TwitterClientError('Reponse does not contain a token.')
        
        if auto_set_token:
            self.auto_set_token(token)
        
        return TwitterObject(token)
    
    def auto_set_token(self, token):
        self.access_token = token['oauth_token']
        self.access_token_secret = token['oauth_token_secret']
        self.session = self.get_oauth_session()
    
    
class AppClient(TwitterClientMixin):
    def __init__(self, consumer_key, consumer_secret, access_token=None, token_type='bearer',
                 api_version=TWITTER_API_VERSION, base_api_url=TWITTER_BASE_API_URL):
        
        self.api_version = api_version
        self.base_api_url = base_api_url
        
        self.request_token_url = '%s/oauth2/token' % self.base_api_url
        self.invalidate_token_url = '%s/oauth2/invalidate_token' % self.base_api_url
        
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.token_type = token_type
        
        self.session = self.get_oauth_session()
        self.auth = HTTPBasicAuth(self.consumer_key, self.consumer_secret)
        self.api = ApiComponent(self)
    
    def get_oauth_session(self):
        client = BackendApplicationClient(self.consumer_key)
        token = None
        
        if self.access_token:
            token = {'access_token': self.access_token, 'token_type': self.token_type }
        
        return OAuth2Session(client=client, token=token)
    
    def get_access_token(self, auto_set_token=True):
        data = {'grant_type': 'client_credentials'}
        
        try:
            response = self.session.post(self.request_token_url, auth=self.auth, data=data)
            data = json.loads(response.content.decode('utf-8'))
            access_token = data['access_token']
        except requests.RequestException as e:
            raise TwitterClientError(str(e))
        except (ValueError, KeyError):
            raise TwitterClientError('Response does not contain an access token.')
        
        if auto_set_token:
            self.access_token = access_token
            self.session = self.get_oauth_session()
        
        return access_token
    
    def invalidate_access_token(self):
        data = {'access_token': self.access_token}
        
        try:
            response = self.session.post(self.invalidate_token_url, auth=self.auth, data=data)
        except requests.RequestException as e:
            raise TwitterClientError(str(e))
        else:
            if response.status_code == 200:
                access_token = self.access_token
                self.access_token = None
                self.session = self.get_oauth_session()
                return access_token
        
        raise TwitterClientError('Could not invalidate access token.')
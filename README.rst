birdy
=====

``birdy`` is a super awesome Twitter API client for Python.

TL;DR
-----

Import client and initialize it:

.. code-block:: python

    from birdy.twitter import UserClient
    client = UserClient(CONSUMER_KEY,
                        CONSUMER_SECRET,
                        ACCESS_TOKEN,
                        ACCESS_TOKEN_SECRET)
                       
GET example (**GET users/show**):

.. code-block:: python

    response = client.api.users.show.get(screen_name='twitter')
    response.data

POST example (**POST statuses/update**):

.. code-block:: pyhton

    response = client.api.statuses.update.post(status='Hello @pybirdy!')

Dynamic URL example (**POST statuses/destroy/:id**)

.. code-block:: python

    response = client.api.statuses.destroy['240854986559455234'].post()


Why another Python Twitter API client? Aren't there enough?
-----------------------------------------------------------

The concept behind ``birdy`` is so simple and awesome that it just had to be done, and the result is a super light weight and easy to use API client, that covers the whole Twitter REST API in just a little over 300 lines of code.

To achieve this, ``birdy`` relies on established, battle tested python libraries like ``requests`` and ``requests-ouath`` to do the heavy lifting, but more importantly it relies on Python's dynamic nature to automatically construct API calls (no individual wrapper functions for API resources needed). This allows ``birdy`` to cover all existing Twitter API resources and any future additions, without the need to update ``birdy`` itself.

Includes full support for both **OAuth1** (user) and **OAuth2** (application) authentication workflows.

Finally, ``birdy`` is simple and explicit by design, besides error handling and JSON decoding it doesn't process the returned data in any way, that is left for you to handle (who'd know better what to do with it).


OK, I'm sold, but how do I use it? How does this dynamic API construction work?
-------------------------------------------------------------------------------

The easiest way to show you is by example. Lets say you want to query Twitter for @twitter user information. The Twitter API resource for this is **GET users/show** (`Twitter docs <https://dev.twitter.com/docs/api/1.1/get/users/show>`_).

First you will need to import a client, here we import UserClient (OAuth1) and than initialize it.

.. code-block:: python

    from birdy.twitter import UserClient
    client = UserClient(CONSUMER_KEY,
                        CONSUMER_SECRET,
                        ACCESS_TOKEN,
                        ACCESS_TOKEN_SECRET)

To query the **GET /users/show** API resource and pass in the parameter screen_name='twitter' you do this.

.. code-block:: python

    resource = client.api.users.show
    response = resource.get(screen_name='twitter')

What happens here is very simple, ``birdy`` translates the ``users.show`` part after ``client.api`` into the appropriate API resource path (**'users/show'**). Then when you call get() on the resource, ``birdy`` constructs a full resource URL, appends any  parameters passed to get() to it and makes a GET request to that URL and returns the result.

Usually the above example would be shortened to just one line like this.

.. code-block:: python

    response = client.api.users.show.get(screen_name='twitter')

Making a post request is similar, if for example, you would like to post a status update, this is how to do it. The API resource is **POST statuses/update** (`Twitter docs <https://dev.twitter.com/docs/api/1.1/post/statuses/update>`_).

.. code-block:: python

    response = client.api.statuses.update.post(status='Hello @pybirdy!')

Like before the part after ``client.api`` gets converted to the correct path, only this time post() is called instead of get(), so ``birdy`` makes a POST request and pass parameters (and files) as part of the request body.

For cases when dynamic values are part of the API resource URL, like when deleting a tweet at **POST statuses/destroy/:id** (`Twitter docs <https://dev.twitter.com/docs/api/1.1/post/statuses/destroy/:id>`_), ``birdy`` supports an alternative, dictionary lookup like, syntax. For example, deleting a tweet with id '240854986559455234' looks like this.

.. code-block:: python

    response = client.api.statuses.destroy['240854986559455234'].post()

By now it should be clear what happens above, ``birdy`` builds the API resource path and than makes a POST request, the only difference is that part of the API path is provided like a dictionary key lookup. 

Actually any call can be written in this alternative syntax, use whichever you prefer. Both syntax forms can be freely combined as in the example above. Some more examples:

.. code-block:: python

    response = client.api['users/show'].get(screen_name='twitter')

    response = client.api['users']['show'].get(screen_name='twitter')

    response = client.api['statuses/destroy']['240854986559455234'].post()


Great, what about authorization? How do I get my access tokens?
--------------------------------------------------------

Before you get started, you will need to `register <https://dev.twitter.com/apps>`_ your application with Twitter, to obtain your application's ``CONSUMER_KEY`` and ``CONSUMER_SECRET``.

``birdy`` supports both **OAuth1** and **OAuth2** authentication workflows by providing two different clients, a ``UserClient`` and ``AppClient`` respectively. While requests to API resources, like in above examples are the same in both clients, the workflow for obtaining access tokens is slightly different.

OAuth1 workflow for user authenticated requests (UserClient)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Step 1: Creating a client instance 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First you need to import the ``UserClient`` and create an instance with your apps ``CONSUMER_KEY`` and ``CONSUMER_SECRET``.

.. code-block:: python

    from birdy.twitter import UserClient

    CONSUMER_KEY = 'YOUR_APPS_CONSUMER_KEY'
    CONSUMER_SECRET = 'YOUR_APPS_CONSUMER_SECRET'
    CALLBACK_URL = 'https://127.0.0.1:8000/callback'

    client = UserClient(CONSUMER_KEY, CONSUMER_SECRET)

Step 2: Get request token and authorization URL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Pass ``callback_url`` only if you have a Web app, Desktop and Mobile apps **do not** require it.

Next you need to fetch request token from Twitter. If you are building a "Sign-in with Twitter" type application it's done like this.

.. code-block:: python

    token = client.get_signin_token(CALLBACK_URL)

Otherwise like this.

.. code-block:: python

    token = client.get_authorize_token(CALLBACK_URL)

Save ``token.oauth_token`` and ``token.oauth_token_secret`` for later user, as this are not the final token and secret.

.. code-block:: python

    ACCESS_TOKEN = token.oauth_token
    ACCESS_TOKEN_SECRET = token.oauth_token_secret

Direct the user to Twitter authorization url obtained from ``token.auth_url``.

Step 3: OAuth verification
~~~~~~~~~~~~~~~~~~~~~~~~~~

    If you have a Desktop or Mobile app, ``OAUTH_VERIFIER`` is the PIN code, you can skip the part about extraction.

After authorizing your application on Twitter, the user will be redirected back to the ``callback_url`` provided during client initialization in *Step 1*.

You will need to extract the ``OAUTH_VERIFIER`` from the URL. Most web frameworks provide an easy way of doing this or you can parse the URL yourself using ``urlparse`` module (if that is your thing).

Django and Flask examples:

.. code-block:: python
    
    #Django
    OAUTH_VERIFIER = request.GET['oauth_verifier']

    #Flash
    OAUTH_VERIFIER = request.args.get('oauth_verifier')

Once you have the ``OAUTH_VERIFIER`` you can use it to obtain the final access token and secret. To do that you will need to create a new instance of ``UserClient``, this time also passing in ``ACCESS_TOKEN`` and ``ACCESS_TOKEN_SECRET`` obtained in *Step 2* and then fetch the tokens.

.. code-block:: python

    client = UserClient(CONSUMER_KEY, CONSUMER_SECRET,
                        ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    
    token = client.get_access_token(OAUTH_VERIFIER)

Now that you have the final access token and secret you can save ``token.oauth_token`` and ``token.oauth_token_secret`` to the database for later use, also you can use the client to start making API request immediately. For example, you can retrieve the users home timeline like this.

.. code-block:: python

    response = client.api.statuses.home_timeline.get()
    response.data

That's it you have successfully authorized the user, retrieved the tokens and can now make API calls on their behalf.


OAuth2 workflow for app authenticated requests (AppClient)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Step 1: Creating a client instance 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For OAuth2 you will be using the ``AppClient``, so first you need to import it and create an instance with your apps ``CONSUMER_KEY`` and ``CONSUMER_SECRET``.

.. code-block:: python

    from birdy.twitter import AppClient

    CONSUMER_KEY = 'YOUR_APPS_CONSUMER_KEY'
    CONSUMER_SECRET = 'YOUR_APPS_CONSUMER_SECRET'

    client = AppClient(CONSUMER_KEY, CONSUMER_SECRET)

Step 2: Getting the access token
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OAuth2 workflow is much simpler compared to OAuth1, to obtain the access token you simply do this.

.. code-block:: python

    access_token = client.get_access_token()

That's it, you can start using the client immediately to make API request on behalf of the app. It's recommended you save the ``access_token`` for later use. You initialize the client with a saved token like this.

.. code-block:: python

    client = AppClient(CONSUMER_KEY, CONSUMER_SECRET, SAVED_ACCESS_KEY)

from django.conf import settings

import stripe


__author__ = 'Ricardo'
__version__ = '0.1'


class StripeSingleton():

    __client = None

    @classmethod
    def __get_connection(self):
        """
        This method create our client
        """

        stripe.api_key = settings.STRIPE_SECRET_KEY

        return stripe

    def __new__(cls, *args, **kwargs):

        if cls.__client == None:

            # making connection
            cls.__client = cls.__get_connection()

        return cls.__client

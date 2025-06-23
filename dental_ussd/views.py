# We will define our USSD View here
# # This will be the main entry point for our USSD application
# We will define our USSD View here
# This will be the main entry point for our USSD application
import os
import yaml

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication
from ussd.core import UssdEngine, UssdRequest

class CustomUssdRequest(UssdRequest):
    """
    Custom extension of UssdRequest class that handles screen loading from YAML journey files.
    """
    def get_screens(self, screen_name=None):
        """
        Load screens from a YAML journey file.
        Args:
            screen_name (str, optional): Name of the screen to retrieve.
        Returns:
            dict or str: Screen content from the journey file.
        Raises:
            FileNotFoundError: If journey file doesn't exist.
            ValueError: If journey file format is invalid or screen not found.
        """
        journey_file = getattr(self, 'journey_file', settings.DEFAULT_USSD_SCREEN_JOURNEY)
        if not os.path.exists(journey_file):
            raise FileNotFoundError(f"Journey file not found: {journey_file}")
        with open(journey_file, 'r') as f:
            journey_content = yaml.safe_load(f)
        if not isinstance(journey_content, dict):
            raise ValueError(f"Invalid journey file format: {journey_content}")
        screen_content = journey_content.get(screen_name)
        if screen_content is None:
            raise ValueError(f"Screen not found: {screen_name}")
        if not isinstance(screen_content, (dict, str)):
            raise ValueError(f"Invalid screen content for {screen_name}")
        return screen_content

@method_decorator(csrf_exempt, name='dispatch')  # Exempt this view from CSRF verification
class DentalAppUssdGateway(APIView):
    """
    API view that serves as the gateway for the Dental App USSD service.
    Handles USSD requests and returns appropriate responses.
    """
    permission_classes = [AllowAny]  # Allow any user to access this API
    authentication_classes = [TokenAuthentication]  # Use token authentication

    def add_cors_headers(self, response, request):
        """
        Add CORS headers to the response.
        This method is added to handle CORS issues (since we will be accessing the API from our Simulator).
        THis is not required for production.
        Args:
            response (Response): The response object to modify.
            request (Request): The incoming request.
        Returns:
            Response: The modified response with CORS headers.
        """
        origin = request.headers.get('Origin', '*')
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Vary'] = 'Origin'
        return response

    def options(self, request, *args, **kwargs):
        """
        Handle OPTIONS requests for CORS preflight checks.
        This method is added to handle CORS issues (since we will be accessing the API from our Simulator).
        THis is not required for production.
        Args:
            request (Request): The incoming request.
            *args, **kwargs: Additional arguments.
        Returns:
            Response: A response with CORS headers.
        """
        response = Response({
            'status': 'success',
            'message': 'Allowed methods: GET, POST, OPTIONS',
            'allowed_methods': ['GET', 'POST', 'OPTIONS']
        }, status=200)
        self.add_cors_headers(response, request)
        return response

    def post(self, request):
        """
        Handle POST requests containing USSD data.
        Args:
            request (Request): The incoming request with USSD data.
            The request should contain the following fields:
            - sessionId (str): The session ID.
            - phoneNumber (str): The phone number of the user.
            - MSG (str): The USSD message.
            - use_built_in_session_management (bool, optional): Whether to use built-in session management. Defaults to False.
            - session_data (dict, optional): Additional session data. Defaults to None.
        Returns:
            Response: The USSD response to be sent back to the user.
        """
        # Parse input text
        try:
            list_of_inputs = request.data['MSG'].split('*')
            text = "*" if len(list_of_inputs) >= 2 and list_of_inputs[-1] == "" and list_of_inputs[-2] == "" else list_of_inputs[-1]
        except KeyError as e:
            response = Response({
                'status': 'error',
                'MSG': f"Missing required field: {e}",
                'MSGTYPE': 'END'
            })
            self.add_cors_headers(response, request)
            return response

        # Create CustomUssdRequest
        session_id = request.data['sessionId']
        if request.data.get('use_built_in_session_management', False):
            session_id = None

        ussd_request = CustomUssdRequest(
            phone_number=request.data['phoneNumber'].strip('+'),
            session_id=session_id,
            ussd_input=text,
            service_code = request.data['serviceCode'],
            language = request.data.get('language', 'en'),
            use_built_in_session_management=request.data.get('use_built_in_session_management', False),
            journey_name = "simple_patient_journey"
        )

        # Process the USSD request using the USSD engine
        ussd_engine = UssdEngine(ussd_request)
        ussd_response = ussd_engine.ussd_dispatcher()
        response = self.ussd_response_handler(ussd_response)

        self.add_cors_headers(response, request)
        return response

    def ussd_response_handler(self, ussd_response):
        """
        Format the USSD response into the required format.
        Args:
            ussd_response: The response from the USSD engine.
        Returns:
            Response: A formatted API response with USSD message and type.
        """
        msg_type = 'CON' if ussd_response.status else 'END'
        if self.request.data.get('serviceCode') == 'test':
            msg_type ='TEST'
        response_data = {
            'status': 'success',
            'MSG': str(ussd_response),
            'MSGTYPE': msg_type
        }
        return Response(response_data)
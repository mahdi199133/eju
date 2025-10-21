# booking/sms_service.py
import os
from dotenv import load_dotenv

load_dotenv()

class SmsService:
    """Base class for SMS services."""
    def send(self, receptor, message):
        raise NotImplementedError("Subclasses must implement this method.")

class LogSmsService(SmsService):
    """A service that 'sends' SMS by logging them to the console."""
    def send(self, receptor, message):
        print("--- [SMS LOG] ---")
        print(f"Receptor: {receptor}")
        print(f"Message: {message}")
        print("-------------------")

class KavenegarSmsService(SmsService):
    """
    An example implementation for Kavenegar SMS gateway.
    This is commented out as it requires a real API key.
    To use it:
    1. pip install kavenegar
    2. Uncomment this class.
    3. Set KAVENEGAR_API_KEY in your .env file.
    4. Change get_sms_service() to return an instance of this class.
    """
    # def __init__(self):
    #     from kavenegar import KavenegarAPI
    #     self.api_key = os.getenv("KAVENEGAR_API_KEY")
    #     if not self.api_key:
    #         raise ValueError("KAVENEGAR_API_KEY is not set in .env file")
    #     self.api = KavenegarAPI(self.api_key)

    # def send(self, receptor, message):
    #     try:
    #         params = {
    #             'receptor': receptor,
    #             'message': message,
    #         }
    #         self.api.sms_send(params)
    #         print(f"SMS sent to {receptor} via Kavenegar.")
    #     except Exception as e:
    #         print(f"Error sending SMS via Kavenegar: {e}")
    #         # Fallback or error handling
    #         LogSmsService().send(receptor, f"KAVENEGAR FAILED: {message}")


def get_sms_service() -> SmsService:
    """
    Returns an instance of the currently configured SMS service.
    Change this function to switch between services (e.g., LogSmsService, KavenegarSmsService).
    """
    return LogSmsService()

import hmac
import json
import logging
from hashlib import sha256

import requests
from ckan.plugins.toolkit import request
from ckanext.subscribe.controller import SubscribeController

log = logging.getLogger(__name__)


class OgdchSubscribeController(SubscribeController):
    def validate_and_signup(self):
        # Send data to Mosparo for verification. See
        # https://documentation.mosparo.io/docs/integration/custom/#performing-verification
        submit_token = request.POST.get("_mosparo_submitToken")
        mosparo_validation_token = request.POST.get("_mosparo_validationToken")
        email = request.POST.get("email").replace("\r\n", "\n")
        form_data = {
            "email": email,
            "_mosparo_submitToken": submit_token,
            "_mosparo_validationToken": mosparo_validation_token,
        }
        public_key = "PRIVATE_KEY"
        private_key = "PUBLIC_KEY"

        form_signature = hmac.new(
            private_key,
            json.dumps(form_data),
            sha256
        ).hexdigest()
        validation_signature = hmac.new(
            private_key,
            mosparo_validation_token + form_signature,
            sha256
        ).hexdigest()

        api_endpoint = "/api/v1/verification/verify"
        request_data = {
            'submitToken': submit_token,
            'validationSignature': validation_signature,
            'formSignature': form_signature,
            'formData': form_data,
        }
        request_signature = hmac.new(
            private_key,
            api_endpoint + json.dumps(request_data),
            sha256
        ).hexdigest()

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        log.warning((public_key, request_signature))
        log.warning(json.dumps(request_data))

        r = requests.post(
            'http://localhost:8080' + api_endpoint,
            data=json.dumps(request_data),
            auth=(public_key, request_signature),
            headers=headers,
            verify=False
        )
        log.warning(r.text)

        return self.signup()

import unittest

from spikes.m0a.provider_contract import (
    InvalidKeyError,
    ProviderFailure,
    ProviderNetworkError,
    ProviderTimeoutError,
    QuotaExhaustedError,
    UnsupportedModelError,
    call_once,
)


class ProviderContractTests(unittest.TestCase):
    def test_mock_errors_are_classified_without_retry(self):
        cases = (
            (InvalidKeyError, "invalid_key"),
            (QuotaExhaustedError, "quota_exhausted"),
            (ProviderTimeoutError, "timeout"),
            (ProviderNetworkError, "network_failure"),
            (UnsupportedModelError, "unsupported_model"),
        )
        for error_type, expected_kind in cases:
            with self.subTest(kind=expected_kind):
                calls = []

                def fail_once(_request):
                    calls.append(1)
                    raise error_type("synthetic mock failure")

                with self.assertRaises(ProviderFailure) as caught:
                    call_once(fail_once, {"synthetic": True})
                self.assertEqual(caught.exception.kind, expected_kind)
                self.assertEqual(len(calls), 1)

    def test_empty_responses_are_rejected(self):
        for response in (None, "", [], {}):
            with self.subTest(response=response):
                with self.assertRaises(ProviderFailure) as caught:
                    call_once(lambda _request: response, {"synthetic": True})
                self.assertEqual(caught.exception.kind, "empty_response")

    def test_successful_mock_response_is_returned(self):
        response = {"text": "synthetic response"}
        self.assertEqual(
            call_once(lambda _request: response, {"synthetic": True}),
            response,
        )


if __name__ == "__main__":
    unittest.main()

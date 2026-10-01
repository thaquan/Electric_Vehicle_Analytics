import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fabric_test_api import Client, WORKSPACE, operation_url


class TestWorkspaceGuard(unittest.TestCase):
    def test_other_workspaces_and_hosts_are_rejected_before_authentication(self):
        client = Client()
        with patch.object(client, "token", side_effect=AssertionError("No token should be requested")):
            for url in [
                "https://api.fabric.microsoft.com/v1/workspaces/5fe78794-25c3-41ee-b35e-bc56542d2cea/items",
                "https://api.powerbi.com/v1.0/myorg/groups/other/datasets",
                "https://onelake.blob.fabric.microsoft.com/other/item/Files/a",
                f"https://example.com/{WORKSPACE}/",
                f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE}/../other/items",
            ]:
                with self.assertRaises(ValueError):
                    client.request(url, "POST", {})

    def test_operation_polling_uses_public_endpoint(self):
        op = "410f4fc2-8ca1-4ab8-a8cb-0f04a5fea3fe"
        self.assertEqual(operation_url({"X-Ms-Operation-Id": op}),
                         "https://api.fabric.microsoft.com/v1/operations/" + op)
        with self.assertRaises(ValueError):
            operation_url({"Location": "https://example.com/operation"})


if __name__ == "__main__":
    unittest.main()

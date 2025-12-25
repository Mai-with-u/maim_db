
import asyncio
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from maim_db.core import init_database, AgentConfigManager, close_database
from maim_db.core.models import APIProviderModel, AGENT_CONFIG_MODELS

from peewee import SqliteDatabase

def verify_secure_model():
    print("=== BEGIN SECURE MODEL CONFIG VERIFICATION ===")
    
    # 1. Init In-Memory DB
    print("[1] Initializing In-Memory Database...")
    test_db = SqliteDatabase(":memory:")
    test_db.bind(AGENT_CONFIG_MODELS, bind_refs=False, bind_backrefs=False)
    test_db.connect()
    test_db.create_tables(AGENT_CONFIG_MODELS)
    
    agent_id = "agent_test_security"
    manager = AgentConfigManager(agent_id)
    
    # 2. Save Config with Real Key
    print("[2] Saving config with REAL API Key...")
    payload = {
        "config_overrides": {
            "model": {
                "api_providers": [
                    {
                        "name": "private_provider",
                        "base_url": "https://api.example.com",
                        "api_key": "sk-real-secret-key-12345",
                        "client_type": "openai"
                    }
                ],
                "models": [
                    {
                        "name": "my-gpt-4",
                        "model_identifier": "gpt-4",
                        "api_provider": "private_provider",
                        "temperature": 0.5
                    }
                ]
            }
        }
    }
    manager.update_config_from_json(payload)
    
    # 3. Verify DB Content
    print("[3] Verifying Database Content (should be REAL key)...")
    provider = APIProviderModel.get(APIProviderModel.name == "private_provider")
    print(f"    DB Stored Key: {provider.api_key}")
    assert provider.api_key == "sk-real-secret-key-12345", "Database should store real key"
    
    # 4. Verify Masked Read
    print("[4] Verifying Masked Read (should be ********)...")
    config_masked = manager.get_all_configs(mask_secrets=True)
    masked_key = config_masked["config_overrides"]["model"]["api_providers"][0]["api_key"]
    print(f"    Masked Read Key: {masked_key}")
    assert masked_key == "********", "API read should return masked key"
    
    # 5. Verify Unmasked Read (Internal)
    print("[5] Verifying Unmasked Read (should be REAL key)...")
    config_full = manager.get_all_configs(mask_secrets=False)
    real_read_key = config_full["config_overrides"]["model"]["api_providers"][0]["api_key"]
    print(f"    Unmasked Read Key: {real_read_key}")
    assert real_read_key == "sk-real-secret-key-12345", "Internal read should return real key"
    
    # 6. Verify Update with Masked Key (Preservation)
    print("[6] Updating config with MASKED Key (should preserve real key)...")
    # Simulate frontend sending back the masked payload with a change to base_url
    update_payload = config_masked
    update_payload["config_overrides"]["model"]["api_providers"][0]["base_url"] = "https://new.example.com"
    # Key is still "********" in this payload
    
    manager.update_config_from_json(update_payload)
    
    provider_updated = APIProviderModel.get(APIProviderModel.name == "private_provider")
    print(f"    Updated DB Key: {provider_updated.api_key}")
    print(f"    Updated DB URL: {provider_updated.base_url}")
    
    assert provider_updated.api_key == "sk-real-secret-key-12345", "Update with mask should preserve original key"
    assert provider_updated.base_url == "https://new.example.com", "Other fields should be updated"
    
    # 7. Verify Update with NEW Real Key (Change key)
    print("[7] Updating with NEW Real Key...")
    update_payload["config_overrides"]["model"]["api_providers"][0]["api_key"] = "sk-new-super-secret"
    manager.update_config_from_json(update_payload)
    
    provider_new = APIProviderModel.get(APIProviderModel.name == "private_provider")
    print(f"    New DB Key: {provider_new.api_key}")
    assert provider_new.api_key == "sk-new-super-secret", "Update with new key should change DB"
    
    # 8. Verify Base URL Masking
    print("[8] Verifying Base URL Masking...")
    # Masked read check
    config_masked = manager.get_all_configs(mask_secrets=True)
    masked_url = config_masked["config_overrides"]["model"]["api_providers"][0]["base_url"]
    print(f"    Masked Read URL: {masked_url}")
    assert masked_url == "********", "API read should return masked URL"
    
    # Update preservation check
    update_payload = config_masked
    manager.update_config_from_json(update_payload)
    
    provider_preserved = APIProviderModel.get(APIProviderModel.name == "private_provider")
    print(f"    Preserved DB URL: {provider_preserved.base_url}")
    assert provider_preserved.base_url == "https://new.example.com", "Update with masked URL should preserve original URL"

    print("=== VERIFICATION SUCCESS ===")

if __name__ == "__main__":
    verify_secure_model()

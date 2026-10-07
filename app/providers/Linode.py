import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("LINODE_API_TOKEN")
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
}

url = "https://api.linode.com/v4/linode/instances?page_size=500"
response = requests.get(url, headers=headers)
if response.status_code == 200:
    all_vms = {vm["id"]: vm["label"] for vm in response.json().get("data", [])}
    fw_url = "https://api.linode.com/v4/networking/firewalls?page_size=500"
    firewall_response = requests.get(fw_url, headers=headers)
    firewalls = firewall_response.json().get("data", [])
    vm_to_firewalls = {}
    for fw in firewalls:
        fw_label = fw.get("label", "Unknown")
        entities = fw.get("entities", [])
        for entity in entities:
            id = None
            if entity.get("type") == "linode":
                id = entity.get("id")
            elif entity.get("type") == "linode_interface":
                parent = entity.get("parent_entity") or {}
                if parent.get("type") == "linode":
                    id = parent.get("id")
            if id:
                if id not in vm_to_firewalls:
                    vm_to_firewalls[id] = []
                if fw_label not in vm_to_firewalls[id]:
                    vm_to_firewalls[id].append(fw_label)
    protected_count = len(vm_to_firewalls)
    unprotected_count = len(all_vms) - protected_count
    print(f"Total VMs: {len(all_vms)}")
    print(f"Protected VMs: {protected_count}")
    print("FIREWALL STATUS")
    for id, vm_label in all_vms.items():
        if id in vm_to_firewalls:
            fw_names = ", ".join(vm_to_firewalls[id])
            print(f"ID: {id} | Label: {vm_label} | Firewall: {fw_names}")
        else:
            print(f"ID: {id} | Label: {vm_label} | Firewall: NO CLOUD FIREWALL")
else:
    print(f"Failed to fetch Linodes. Status Code:{response.status_code}")
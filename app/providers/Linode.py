import os
import requests
from dotenv import load_dotenv
import asyncio
load_dotenv()
API_TOKEN = os.getenv("LINODE_API_TOKEN")
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
}
url = "https://api.linode.com/v4/linode/instances?page_size=500"
async def monitor_firewalls():
    def check_firewalls():
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch Linodes. Status Code: {response.status_code}")
            return
        all_vms = {
            vm["id"]: vm["label"]
            for vm in response.json().get("data", [])
        }
        fw_url = "https://api.linode.com/v4/networking/firewalls?page_size=500"
        firewall_response = requests.get(
            fw_url, headers=headers, timeout=30
        )
        if firewall_response.status_code != 200:
            print("Failed to fetch firewalls:", firewall_response.status_code)
            return
        firewalls = firewall_response.json().get("data", [])
        vm_to_firewalls = {}
        for fw in firewalls:
            fw_label = fw.get("label", "Unknown")
            for entity in fw.get("entities", []):
                vm_id = None
                if entity.get("type") == "linode":
                    vm_id = entity.get("id")
                elif entity.get("type") == "linode_interface":
                    parent = entity.get("parent_entity") or {}

                    if parent.get("type") == "linode":
                        vm_id = parent.get("id")
                if vm_id is not None:
                    vm_to_firewalls.setdefault(vm_id, [])
                    if fw_label not in vm_to_firewalls[vm_id]:
                        vm_to_firewalls[vm_id].append(fw_label)
        protected_count = sum(
            1 for vm_id in all_vms if vm_to_firewalls.get(vm_id)
        )
        unprotected_count = len(all_vms) - protected_count
        print("\n========== FIREWALL STATUS ==========")
        print(f"Total VMs: {len(all_vms)}")
        print(f"Protected VMs: {protected_count}")
        print(f"Unprotected VMs: {unprotected_count}")
        for vm_id, vm_label in all_vms.items():
            if vm_to_firewalls.get(vm_id):
                fw_names = ", ".join(vm_to_firewalls[vm_id])
                print(f"ID: {vm_id} | Label: {vm_label} | Firewall: {fw_names}")
            else:
                print(
                    f"ID: {vm_id} | Label: {vm_label} | "
                    "Firewall: NO CLOUD FIREWALL"
                )
    await asyncio.to_thread(check_firewalls)
async def repeat_monitoring():
    while True:
        try:
            await monitor_firewalls()
        except Exception as e:
            print(f"Monitoring error: {e}")
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(repeat_monitoring())

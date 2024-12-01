from locust import HttpUser, task, between
import random

class WalletUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        # Create test wallet
        response = self.client.post("/api/v1/wallets/")
        self.wallet_id = response.json()["id"]
        # Initial deposit
        self.client.post(
            f"/api/v1/wallets/{self.wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": "1000.00"}
        )

    @task(3)
    def make_transaction(self):
        amount = random.uniform(1, 100)
        op_type = random.choice(["DEPOSIT", "WITHDRAW"])
        self.client.post(
            f"/api/v1/wallets/{self.wallet_id}/operation",
            json={
                "operation_type": op_type,
                "amount": f"{amount:.2f}"
            }
        )

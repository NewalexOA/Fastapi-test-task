from locust import HttpUser, task, between
import random

class WalletUser(HttpUser):
    wait_time = between(0.01, 0.05)
    
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
    def get_wallet(self):
        # Reading wallet (light operation)
        self.client.get(f"/wallets/{self.wallet_id}")
    
    @task(1)
    def create_wallet(self):
        # Creating wallet (medium operation)
        self.client.post("/wallets/")
    
    @task(2)
    def deposit(self):
        # Deposit (heavy operation)
        self.client.post(f"/wallets/{self.wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": "100.00"})

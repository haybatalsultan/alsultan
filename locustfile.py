from locust import HttpUser, between, task


class StoreUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(5)
    def home(self):
        self.client.get("/")

    @task(8)
    def catalog(self):
        self.client.get("/catalog/")

    @task(2)
    def search(self):
        self.client.get("/catalog/?q=amber")

class PaymentService:
    """Phase 1 boundary. No online payment provider is implemented."""

    def create_session(self, *args, **kwargs):
        raise NotImplementedError("Online payment is disabled in Version 1.")

    def handle_webhook(self, *args, **kwargs):
        raise NotImplementedError("Online payment is disabled in Version 1.")

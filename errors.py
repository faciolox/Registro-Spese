class DescriptionError(Exception):
    def __init__(self, messaggio):
        super().__init__(messaggio)
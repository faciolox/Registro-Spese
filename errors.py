class DescriptionError(Exception):
    def __init__(self, messaggio):
        super().__init__(messaggio)

class CreateUserError(Exception):
    def __init__(self, messaggio):
        super().__init__(messaggio)
        
class BudgetNotFound(Exception):
    def __init__(self, messaggio):
        super().__init__(messaggio)
class NoAddebitoError(Exception):
    def __init__(self, messaggio):
        super().__init__(messaggio)
class GenericError(Exception):
    def __init__(self, messaggio):
        super().__init__(messaggio)
        
class DeleteError(Exception):
    def __init__(self, messaggio):
        super().__init__(messaggio)

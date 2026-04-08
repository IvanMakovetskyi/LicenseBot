class UserService:
    @staticmethod
    def getStartText() -> str:
        return "Hello! Bot is working."
    
    @staticmethod
    def getStatusText() -> str:
        return "Your status is unknown :("
    
    @staticmethod
    def getEchoText(text: str) -> str:
        return f"Hey, you said: {text}"

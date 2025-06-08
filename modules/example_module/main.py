"""
Example module for ELLMa demonstrating the module structure and documentation.
"""

class ExampleModule:
    """
    An example module that demonstrates the structure and documentation
    required for ELLMa modules.
    """
    
    def __init__(self):
        """Initialize the example module."""
        self.name = "Example Module"
        self.version = "0.1.0"
    
    def example_method(self, input_value: str = None) -> dict:
        """
        An example method that processes input and returns a result.
        
        Args:
            input_value: Optional input string to process
            
        Returns:
            dict: A dictionary containing the processed result
            
        Example:
            >>> module = ExampleModule()
            >>> result = module.example_method("test")
            >>> "result" in result
            True
        """
        if input_value is None:
            input_value = "default"
            
        return {
            "status": "success",
            "result": f"Processed: {input_value}",
            "module": self.name,
            "version": self.version
        }
    
    def get_commands(self) -> dict:
        """
        Return the commands provided by this module.
        
        Returns:
            dict: Dictionary of command names and their corresponding methods
        """
        return {
            "example_command": self.example_method
        }

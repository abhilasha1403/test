from abc import abstractmethod

from proj.core.awel import MapOperator
from proj.core.awel.task.base import IN, OUT


class AssemblerOperator(MapOperator[IN, OUT]):
    """The Base Assembler Operator."""

    async def map(self, input_value: IN) -> OUT:
        """Map input value to output value.

        Args:
            input_value (IN): The input value.

        Returns:
            OUT: The output value.
        """
        return await self.blocking_func_to_async(self.assemble, input_value)

    @abstractmethod
    def assemble(self, input_value: IN) -> OUT:
        """assemble knowledge for input value."""

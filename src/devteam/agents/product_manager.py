from .schemas import AskClarification, ProductManagerResponse, SubmitSpecification
from .tool_agent import ToolAgent


class ProductManager(ToolAgent[ProductManagerResponse]):
    output_schema = ProductManagerResponse
    tools = [AskClarification, SubmitSpecification]

    def _map_tool_to_output(self, tool_name: str, tool_args: dict) -> ProductManagerResponse:
        if tool_name == 'AskClarification':
            return ProductManagerResponse(clarification_question=tool_args['question'])
        if tool_name == 'SubmitSpecification':
            return ProductManagerResponse(specs=tool_args['specs'])
        raise ValueError(f"Unexpected tool call: {tool_name}")

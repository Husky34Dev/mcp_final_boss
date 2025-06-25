import json
import logging
import re
from typing import Optional
from framework.tools import format_tool_response

class InlineFunctionHandler:
    def __init__(self, handlers):
        self.handlers = handlers

    def handle_inline_function(self, content_str: str) -> Optional[str]:
        """
        Handles inline function execution logic.
        """
        inline = re.match(r'<function=(\w+)>(\{.*\})\[/function\]', content_str)
        if not inline:
            inline = re.match(r'<(\w+)>(\{.*\})</\1>', content_str)
        if inline:
            fn_name, args_json = inline.group(1), inline.group(2)
            try:
                args = json.loads(args_json)
                result = self.handlers[fn_name](**args)
                formatted_result = format_tool_response(fn_name, result).strip()
                return formatted_result
            except Exception as e:
                logging.error(f"Error executing inline function {fn_name}: {e}")
        return None

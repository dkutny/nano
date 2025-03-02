from nanoengineer.llm_interact import LLMInteract
from prompts import system_prompt, answer_instruction
import re
import json
import logging as lg

class NanoEngineer:
    def __init__(self, llm: LLMInteract, additional_instructions: str=""):
        """
        Initialize NanoEngineer with a given LLM provider.

        Args:
            llm (LLMInteract): An instance of LLMInteract.
            additional_instructions (str): Additional instructions to be added to the system prompt.
        """
        self.llm = llm
        self.logger = lg.getLogger(__name__)
        self.logger.info("Initializing NanoEngineer")

        if len(additional_instructions) > 0:
            full_prompt = f"{system_prompt}\n\nAdditional instructions: {additional_instructions}"
            self.logger.debug(f"Using additional instructions: {additional_instructions}")
        else:
            full_prompt = system_prompt

        self.llm.set_system_prompt(full_prompt)
        self.plans = {}
        self.tools = {}
        self.widgets = {}
        self.answer_instruction = None
        
    def register_tools(self, tools):
        """
        Register tools with NanoEngineer.

        Args:
            tools (list): A list of tool instances to be registered.
        """
        self.logger.info(f"Registering {len(tools)} tools")
        for tool in tools:
            if tool.name in self.tools:
                self.logger.error(f"Tool {tool.name} already registered")
                raise Exception(f"Tool {tool.name} already registered")
            self.tools[tool.name] = tool
            self.logger.debug(f"Registered tool: {tool.name}")

    def set_answer_instruction(self, answer_instruction):
        """
        Set the answer instruction for NanoEngineer.

        Args:
            answer_instruction (str): The answer instruction to be set.
        """
        self.answer_instruction = answer_instruction

    def _format_tools(self):
        tool_list = []

        for t in self.tools:
            elem = {
                "name": t,
                "description": self.tools[t].description,
                "params": self.tools[t].params,
                "return_schema": self.tools[t].return_schema
            }
            
            tool_list.append(elem)

        return json.dumps(tool_list)

    def register_widgets(self, widgets):
        """
        Register widgets with NanoEngineer.

        Args:
            widgets (list): A list of widget instances to be registered.
        """
        self.logger.info(f"Registering {len(widgets)} widgets")
        for w in widgets:
            if w.name in self.widgets:
                self.logger.error(f"Widget {w.name} already registered")
                raise Exception(f"Widget {w.name} already registered")
            self.widgets[w.name] = {
                "name": w.name,
                "description": w.description,
                "params": w.params
            }
            self.logger.debug(f"Registered widget: {w.name}")


    def _format_answer_instruction(self):
        return answer_instruction.format(answer_instruction=self.answer_instruction)

    def send_message(self, message, yield_response=False):
        """
        Send a message to NanoEngineer.

        Args:
            message (str): The message to be sent.
            yield_response (bool): Whether to yield the response.

        Returns:
            str: The response from NanoEngineer.
        """
        self.logger.info("Processing new message")
        self.logger.debug(f"Message content: {message}")

        if len(self.llm.history) == 0:
            msg = f"""Request: {message}\n\nTools: {self._format_tools()}"""

            if len(self.widgets) > 0:
                msg += f"\n\nWidgets: {json.dumps(self.widgets)}"
            self.llm.append(msg)
        else:
            self.llm.append(message)

        retries = 0

        while True:
            response = self.llm.response()
            is_plan, plan = self._is_plan(response)

            if is_plan:
                self.logger.info(f"Received plan {plan['id']} with {len(plan['steps'])} steps")
                self.plans[plan["id"]] = plan["steps"]
                if yield_response:
                    yield self.plans[plan["id"]]

            is_execution, execution = self._is_execution(response)

            if is_execution:
                if execution == "json_unparseable":
                    retries += 1
                    self.logger.warning(f"JSON parse error, retry {retries}/3")
                    if retries > 3:
                        self.logger.error("Max retries reached for JSON parsing")
                        raise Exception("JSON unparseable")
                    else:
                        continue

                self.logger.info(f"Executing tool for plan {execution['plan_id']}")

                result = self.execute_tool(execution["content"])
                self.llm.append(response, "assistant")
                self.llm.append(result)

                if yield_response:
                    yield execution

            if not is_execution:
                self.llm.append(response, "assistant")

                if self.answer_instruction:
                    is_answer, answer = self._is_answer(response)

                    if is_answer:
                        formatted_answer_instruction = self._format_answer_instruction()
                        self.llm.append(formatted_answer_instruction)
                        new_answer = self.llm.response()
                        self.llm.append(new_answer, "assistant")

                if yield_response:
                    yield response
                break
        
        
    def _is_plan(self, response):
        """
        Check if the response contains a plan.

        Args:
            response (str): The response to be checked.

        Returns:
            bool: True if the response contains a plan, False otherwise.
        """
        plan_pattern = r'<Plan id=(\d+)>(.*)</Plan>'
        step_pattern = r'<(\d+)>(.*?)</\1>'
        
        plan_match = re.search(plan_pattern, response, re.DOTALL)
        
        if plan_match:
            plan_id = int(plan_match.group(1))
            steps_content = plan_match.group(2)
            steps = []

            for step_match in re.finditer(step_pattern, steps_content):
                step_num = int(step_match.group(1))
                step_content = step_match.group(2)
                steps.append(step_content)
            
            return True, {"id": plan_id, "steps": steps}
        
        return False, None

    def _is_answer(self, response):
        """
        Check if the response contains an answer.

        Args:
            response (str): The response to be checked.

        Returns:
            bool: True if the response contains an answer, False otherwise.
        """
        answer_pattern = r'<Answer plan=(\d+) step=(\d+)>(.*)</Answer>'
        answer_match = re.search(answer_pattern, response, re.DOTALL)

        if answer_match:
            return True, answer_match

        return False, None

    def execute_tool(self, tool_content):
        """
        Execute a tool.

        Args:
            tool_content (dict): The content of the tool to be executed.

        Returns:
            str: The result of the tool execution.
        """
        tool_name = tool_content["execute_tool"]
        self.logger.info(f"Executing tool: {tool_name}")
        self.logger.debug(f"Tool parameters: {tool_content['params']}")

        if not tool_name in self.tools:
            self.logger.error(f"Tool {tool_name} not found")
            raise Exception(f"Tool {tool_name} not found")

        tool = self.tools[tool_name]()
        
        try:
            tool_result = tool.execute(params=tool_content["params"])
        except Exception as e:
            self.logger.error(f"Tool {tool_name} execution failed: {e}")
            raise Exception(f"Tool {tool_name} execution failed: {e}")
        return tool_result

    def _is_execution(self, response):
        """
        Check if the response contains an execution.

        Args:
            response (str): The response to be checked.

        Returns:
            bool: True if the response contains an execution, False otherwise.
            dict: The execution content if the response contains an execution, None otherwise.
        """
        execution_pattern = r'<Execute plan=(\d+) step=(\d+)>(.*)</Execute>'
        execution_match = re.search(execution_pattern, response, re.DOTALL)

        if execution_match:
            plan_id = int(execution_match.group(1))
            step = int(execution_match.group(2))
            execution_content = execution_match.group(3)

            try:
                execution_content = json.loads(execution_content)
            except:
                return True, "json_unparseable"

            return True, {"plan_id": plan_id, "content": execution_content}

        return False, None

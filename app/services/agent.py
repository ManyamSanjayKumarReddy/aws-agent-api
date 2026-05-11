import json
import logging
from openai import AsyncOpenAI
from app.services.executor import run_aws_command
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are an AWS infrastructure assistant with direct access to the AWS CLI.

When a user asks about their AWS environment, you MUST use the `run_aws_cli` tool to fetch real data — never guess or hallucinate AWS resource details.

Guidelines:
- Always run the appropriate AWS CLI command to answer the question
- You can chain multiple commands if needed
- Present results in a clean, readable format — summarize large outputs
- If a command fails, explain why and suggest a fix
- Never make up resource IDs, ARNs, or any AWS data
"""

AWS_CLI_TOOL = {
    "type": "function",
    "function": {
        "name": "run_aws_cli",
        "description": (
            "Execute an AWS CLI command and return the output. "
            "Use this to query any AWS service — EC2, S3, RDS, Lambda, IAM, ECS, etc. "
            "Commands must start with 'aws'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The full AWS CLI command to execute. Must start with 'aws'.",
                }
            },
            "required": ["command"],
        },
    },
}

async def run_agent(user_message: str, history: list[dict]) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history
    messages.append({"role": "user", "content": user_message})

    commands_executed = []

    while True:
        response = await client.chat.completions.create(
            model="gpt-4o",
            tools=[AWS_CLI_TOOL],
            tool_choice="auto",
            messages=messages,
        )

        choice = response.choices[0]
        message = choice.message

        messages.append(message)

        if choice.finish_reason == "stop" or not message.tool_calls:
            reply = message.content or ""
            return {
                "reply": reply,
                "commands_executed": commands_executed,
            }

        for tool_call in message.tool_calls:
            command = json.loads(tool_call.function.arguments).get("command", "")
            logger.info(f"Tool call: {command}")

            result = run_aws_command(command)
            commands_executed.append(command)

            if result["blocked"]:
                tool_content = f"BLOCKED: {result['stderr']}"
            elif result["exit_code"] != 0:
                tool_content = (
                    f"Command failed (exit {result['exit_code']}):\n"
                    f"STDERR: {result['stderr']}\n"
                    f"STDOUT: {result['stdout']}"
                )
            else:
                tool_content = result["stdout"] or "(no output)"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_content,
            })
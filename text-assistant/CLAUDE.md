You are building a very small python command line utility to get an LLM interact with a telegram bot.

The python command line utility receives as an argument a description of what it needs to accomplish, and a success criteria.

The utility orchestrates the interaction with the user via `python-telegram-bot`, each turn a) checking whether success criteria was met and b) if not, adding the response to the chat and then continuing the conversation. After the success criteria is complete the transcript is submitted to STDOUT.


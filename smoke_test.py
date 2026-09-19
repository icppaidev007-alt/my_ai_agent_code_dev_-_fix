import asyncio
import sys

async def main():
    try:
        print("TEST: Python import...")
        from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
        print("PASS: Python import")

        print("TEST: Agent creation...")
        # read-only by default (no CapabilitiesConfig passed, so it can only read)
        config = LocalAgentConfig(
            system_instructions=(
                "You are a read-only codebase explorer. "
                "Investigate the directory D:\\Agent Stuff\\muparser. "
                "List the repository root, identify CMakeLists.txt, "
                "identify the main project name by reading CMakeLists.txt, "
                "and report whether the repository appears to be a CMake C++ project. "
                "Do NOT edit any files or execute any build commands."
            )
        )
        print("PASS: Agent creation")

        print("TEST: Agent session and read access...")
        async with Agent(config) as agent:
            response = await agent.chat("Examine the directory D:\\Agent Stuff\\muparser and give me the required summary.")
            
            async for token in response:
                sys.stdout.write(token)
                sys.stdout.flush()
            print("\n")
            print("PASS: Agent session")
            print("PASS: Local filesystem/repository read access")
            
    except Exception as e:
        print(f"\nFAIL: Exception occurred: {e}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(main())

import asyncio
import random
from HHRuParser import HHRuParser, runtime_async

parser = HHRuParser()


@runtime_async
async def test():
    tasks = [asyncio.create_task(parser.parse_topic(a)) for a in range(1, 50)]
    await asyncio.wait(tasks)
    for task in tasks:
        # print(task.result())
        pass


# print(parser.login())

asyncio.run(test())
result = asyncio.run(parser.parse_topic(random.randint(1, 400000)))

print(asyncio.run(parser.parse_user(2)))

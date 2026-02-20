# test_observable_agent.py
from tools.registry import registry, Tool
from agent.observable_agent import ObservableAgent

# -------------------------
# 1️⃣ سجل أداة تجريبية
# -------------------------
@registry.register(name="greet", description="Returns a greeting")
def greet_tool():
    return "Hello from the tool!"

@registry.register(name="compute", description="Performs a dummy computation")
def compute_tool():
    return 42

# -------------------------
# 2️⃣ أنشئ الوكيل
# -------------------------
agent = ObservableAgent(verbose=True)

# -------------------------
# 3️⃣ اختبر الوكيل مع استعلامات مختلفة
# -------------------------
queries = [
    "Please greet me",
    "Do some compute",
    "Just a random question"
]

for query in queries:
    print(f"\nUser query: {query}")
    result = agent.run(query)
    print(f"Agent answer: {result['answer']}")
    print(f"Trace: {result['trace']}")

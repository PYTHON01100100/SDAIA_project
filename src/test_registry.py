from tools.registry import registry



@registry.register(
    name="add_numbers",
    description="Add two numbers",
    category="math"
)
def add(a: int, b: int):
    return a + b


def main():
    # اختبار get_tool
    tool = registry.get_tool("add_numbers")
    print("Tool found:", tool is not None)

    # اختبار التنفيذ
    result = tool.execute(a=10, b=5)
    print("Result:", result)

    # اختبار category
    math_tools = registry.get_tools_by_category("math")
    print("Math tools:", [t.name for t in math_tools])


if __name__ == "__main__":
    main()

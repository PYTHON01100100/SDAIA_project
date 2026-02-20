import time

class CostTracker:
    def __init__(self):
        self.query_start_time = None
        self.query_end_time = None
        self.query_text = ""
        self.usage_log = []  # list of dicts per agent

    # -----------------------------------
    # Start query
    # -----------------------------------
    def start_query(self, query_text):
        self.query_start_time = time.time()
        self.query_text = query_text
        self.usage_log = []
        print(f"Started query tracking: {query_text}")

    # -----------------------------------
    # Log agent usage
    # -----------------------------------
    def log_agent_usage(self, agent_name, model, input_tokens, output_tokens):
        self.usage_log.append({
            "agent": agent_name,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        })
        print(f"[{agent_name}] Logged usage: model={model}, input={input_tokens}, output={output_tokens}")

    # -----------------------------------
    # End query
    # -----------------------------------
    def end_query(self):
        self.query_end_time = time.time()
        duration = self.query_end_time - self.query_start_time
        print(f"Ended query tracking. Duration: {duration:.2f}s")

    # -----------------------------------
    # Print cost/usage breakdown
    # -----------------------------------
    def print_cost_breakdown(self):
        print("\n=== Usage Breakdown ===")
        total_input = 0
        total_output = 0
        for usage in self.usage_log:
            print(f"{usage['agent']}: model={usage['model']}, input_tokens={usage['input_tokens']}, output_tokens={usage['output_tokens']}")
            total_input += usage['input_tokens']
            total_output += usage['output_tokens']
        print(f"Total input tokens: {total_input}")
        print(f"Total output tokens: {total_output}")
        print("======================\n")

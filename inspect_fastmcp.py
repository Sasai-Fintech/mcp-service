import inspect
import fastmcp
from fastmcp import FastMCP

print("FastMCP location:", fastmcp.__file__)
try:
    print("\nFastMCP.http_app source:")
    print(inspect.getsource(FastMCP.http_app))
except Exception as e:
    print(f"Could not get source: {e}")


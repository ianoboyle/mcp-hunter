from ApiClient import APIClient


def list_mcp_servers():

    client = APIClient(base_url="https://registry.modelcontextprotocol.io/v0.1/servers")

    for item in client.list():
        print(item)


list_mcp_servers()

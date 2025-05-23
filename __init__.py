# your_plugin_name/__init__.py

from .nodes import PromptSelectorNode, get_node_instance
from aiohttp import web

# 定义一个简单的路由处理器，用于获取指定 node_id 的 keys 列表
@web.middleware
async def handle_get_prompt_keys(request, handler):
    if request.path.startswith('/get_prompt_keys/'):
        try:
            node_id = request.match_info['node_id']
            node = get_node_instance(node_id)
            return web.json_response(node.get_current_keys())
        except KeyError:
            return web.json_response({"error": "Node not found"}, status=404)
    return await handler(request)

def setup_routes(app):
    # 添加中间件以处理 /get_prompt_keys/{node_id} 路径
    app.middlewares.append(handle_get_prompt_keys)

    # 或者你可以直接添加路由（另一种方式）
    # routes = web.RouteTableDef()
    # @routes.get('/get_prompt_keys/{node_id}')
    # async def get_prompt_keys(request):
    #     node_id = request.match_info['node_id']
    #     node = get_node_instance(node_id)
    #     return web.json_response(node.get_current_keys())
    # app.add_routes(routes)

# 如果你需要加载前端页面，可以在这里设置 WEB_DIRECTORY
WEB_DIRECTORY = "./web"  # 相对于插件根目录的前端资源路径

# 注册节点类映射
NODE_CLASS_MAPPINGS = {
    "PromptSelector": PromptSelectorNode
}

# 注册节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptSelector": "提示词选择器"
}
# __init__.py

from .nodes import PromptSelectorNode, get_node_instance
from aiohttp import web

# 定义一个中间件来处理 /get_prompt_keys/{node_id} 的请求
@web.middleware
async def handle_get_prompt_keys(request, handler):
    if request.path.startswith('/get_prompt_keys/'):
        try:
            node_id = request.match_info.get('node_id')
            if not node_id:
                return web.json_response({"error": "Missing node_id"}, status=400)

            node = get_node_instance(node_id)
            return web.json_response(node.get_current_keys())
        except Exception as e:
            return web.json_response({"error": f"Failed to get keys: {str(e)}"}, status=500)
    return await handler(request)


def setup_routes(app):
    """添加自定义路由规则到 AioHTTP 应用中"""
    # 添加中间件以处理 `/get_prompt_keys/{node_id}` 请求路径
    app.middlewares.append(handle_get_prompt_keys)


# 前端页面资源目录（可选）
WEB_DIRECTORY = "./web"

# 节点类映射：ComfyUI 会通过这个字典加载你的节点
NODE_CLASS_MAPPINGS = {
    "PromptSelector": PromptSelectorNode
}

# 节点显示名称映射（在 UI 中显示为中文等友好名称）
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptSelector": "提示词选择器"
}

# 模块导出标识（可选）
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
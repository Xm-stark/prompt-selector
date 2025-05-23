import json
import os

# 全局字典：用于管理每个 node_id 对应的 PromptSelectorNode 实例
prompt_selector_nodes = {}

class PromptSelectorNode:
    """提示词选择器节点，用于在ComfyUI中动态选择预定义的提示词"""

    REPLACE_MODES = ["原始值", "固定句式: 把图片中的[替换对象]替换成[目标对象]"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt_pairs": ("STRING", {
                    "multiline": True,
                    "default": "{\"key1\": \"value1\", \"key2\": \"value2\", \"key3\": \"value3\"}"
                }),
                "selected_key": (["key1", "key2", "key3"],),
                "replace_mode": (cls.REPLACE_MODES, {"default": cls.REPLACE_MODES[0]}),
                "source_word_file": ("STRING", {"default": "", "label": "替换对象文件路径"}),
                "target_word_file": ("STRING", {"default": "", "label": "目标对象文件路径"}),
            },
            "hidden": {"node_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "process"
    CATEGORY = "Prompt Selector"

    def __init__(self):
        self.prompt_dict = {}
        self.keys_list = []
        self._last_pairs = None

    def parse_prompt_pairs(self, prompt_pairs: str) -> None:
        """解析提示词对字符串并更新可用的keys"""
        if prompt_pairs == self._last_pairs:
            return  # 没有变化则跳过

        self.prompt_dict.clear()
        self.keys_list.clear()

        try:
            prompt_dict = json.loads(prompt_pairs)
            if isinstance(prompt_dict, dict):
                self.prompt_dict = prompt_dict
                self.keys_list = list(prompt_dict.keys())
            else:
                raise ValueError("解析结果不是字典类型")
        except json.JSONDecodeError as e:
            print(f"解析JSON时出错: {str(e)}, 输入: {prompt_pairs}")
        except Exception as e:
            print(f"解析提示词对时出错: {str(e)}, 输入: {prompt_pairs}")

        self._last_pairs = prompt_pairs

        # 默认值回退
        if not self.keys_list:
            self.prompt_dict = {"key1": "value1", "key2": "value2", "key3": "value3"}
            self.keys_list = list(self.prompt_dict.keys())

    def get_current_keys(self):
        """返回当前 keys 列表"""
        return {"keys": self.keys_list}

    @staticmethod
    def load_words_from_file(file_path: str) -> list:
        """从文件中读取单词列表（每行一个），支持UTF-8和GBK编码"""
        if not file_path or not os.path.exists(file_path):
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f.readlines() if line.strip()]
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    words = [line.strip() for line in f.readlines() if line.strip()]
            except Exception as e:
                print(f"读取文件失败: {file_path}, 错误: {str(e)}")
                return []
        except Exception as e:
            print(f"读取文件失败: {file_path}, 错误: {str(e)}")
            return []

        return words

    def process(self, prompt_pairs: str, selected_key: str, replace_mode: str,
                source_word_file: str, target_word_file: str, node_id: str) -> tuple:
        """
        处理选择的提示词
        :param node_id: 唯一标识当前节点的 ID
        """
        global prompt_selector_nodes

        # 如果该 node_id 还没有对应的节点实例，则创建一个新的
        if node_id not in prompt_selector_nodes:
            prompt_selector_nodes[node_id] = PromptSelectorNode()

        node = prompt_selector_nodes[node_id]
        node.parse_prompt_pairs(prompt_pairs)

        # 确保选中的 key 存在，否则使用第一个可用的 key
        if selected_key not in node.prompt_dict:
            selected_key = node.keys_list[0] if node.keys_list else "key1"

        selected_value = node.prompt_dict.get(selected_key, "")

        if replace_mode == self.REPLACE_MODES[1]:
            source_words = self.load_words_from_file(source_word_file)
            target_words = self.load_words_from_file(target_word_file)

            results = []
            for source_word, target_word in zip(source_words, target_words):
                result = f"把图片中的{source_word}替换成{target_word}"
                results.append(result)

            return ("\n".join(results),)

        print(f"Processing node with ID: {node_id}")  # 使用 node_id 参数
        return (selected_value,)


def get_node_instance(node_id: str):
    """
    提供给外部接口使用的函数，根据 node_id 获取当前 PromptSelectorNode 实例
    """
    global prompt_selector_nodes

    if node_id not in prompt_selector_nodes:
        prompt_selector_nodes[node_id] = PromptSelectorNode()

    return prompt_selector_nodes[node_id]
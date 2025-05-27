import json
import os
import time

# 全局字典：用于管理每个 node_id 对应的 PromptSelectorNode 实例
prompt_selector_nodes = {}

class PromptSelectorNode:
    """提示词选择器节点，用于在ComfyUI中动态选择预定义的提示词"""

    REPLACE_MODES = ["原始值", "固定句式: 把图片中的[替换对象]替换成[目标对象]"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 主要输入字段
                "prompt_pairs": ("STRING", {
                    "multiline": True,
                    "default": "{\"key1\": \"value1\", \"key2\": \"value2\", \"key3\": \"value3\"}"
                }),
                "selected_key": (["key1", "key2", "key3"],),
                "replace_mode": (cls.REPLACE_MODES, {"default": cls.REPLACE_MODES[0]}),

                # 新增：单个词语输入
                "manual_input": ("STRING", {"default": "", "label": "手动输入词语"}),

                # 替换用文件路径
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

        # 新增：记录文件指针位置
        self.source_index = 0
        self.target_index = 0

    def parse_prompt_pairs(self, prompt_pairs: str) -> None:
        """解析提示词对字符串并更新可用的keys"""
        if prompt_pairs == self._last_pairs:
            return  # 没有变化则跳过

        print(f"[DEBUG] 开始解析 JSON: {prompt_pairs}")

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
            print("[WARNING] 使用默认键值对作为回退")
            self.prompt_dict = {"key1": "value1", "key2": "value2", "key3": "value3"}
            self.keys_list = list(self.prompt_dict.keys())

    def get_current_keys(self):
        """返回当前 keys 列表"""
        return {"keys": self.keys_list}

    @staticmethod
    def load_words_from_file(file_path: str) -> list:
        """从文件中读取单词列表（每行一个），支持UTF-8和GBK编码"""
        if not file_path or not os.path.exists(file_path):
            print(f"[ERROR] 文件不存在或路径为空: {file_path}")
            return []

        print(f"[DEBUG] 正在加载文件: {file_path}")

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

        print(f"[DEBUG] 加载完成，共 {len(words)} 行")
        return words

    def process(self, prompt_pairs: str, selected_key: str, replace_mode: str,
                source_word_file: str, target_word_file: str, manual_input: str, node_id: str) -> tuple:
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

        # 手动输入优先级最高
        if manual_input.strip():
            print(f"[INFO] 使用手动输入: {manual_input}")
            return (f"{manual_input.strip()} [time={int(time.time())}]", )

        # 确保选中的 key 存在，否则使用第一个可用的 key
        if selected_key not in node.prompt_dict:
            if node.keys_list:
                selected_key = node.keys_list[0]
                print(f"[INFO] 使用第一个可用键: {selected_key}")
            else:
                # 最终 fallback
                selected_key = "key1"
                node.prompt_dict[selected_key] = "value1"
                print(f"[INFO] 使用最终 fallback 键: {selected_key}")

        selected_value = node.prompt_dict.get(selected_key, "")

        if replace_mode == self.REPLACE_MODES[1]:
            source_words = self.load_words_from_file(source_word_file)
            target_words = self.load_words_from_file(target_word_file)

            if not source_words or not target_words:
                print("[ERROR] 替换对象或目标对象文件为空")
                return ("替换对象或目标对象文件为空", )

            min_len = min(len(source_words), len(target_words))
            index = max(node.source_index, node.target_index)

            if index >= min_len:
                print("[WARNING] 文件已读取完毕，循环从头开始")
                index = 0
                node.source_index = 0
                node.target_index = 0

            source_word = source_words[index]
            target_word = target_words[index]

            result = f"把图片中的{source_word}替换成{target_word}"

            # 更新索引
            node.source_index += 1
            node.target_index += 1

            print(f"[INFO] 替换模式输出: {result}")
            return (f"{result} [idx={index}]", )

        print(f"[INFO] 返回选定值: {selected_value}")
        print(f"Processing node with ID: {node_id}")  # 使用 node_id 参数

        # 添加唯一标识避免缓存问题
        return (f"{selected_value} [time={int(time.time())}]", )


def get_node_instance(node_id: str):
    """
    提供给外部接口使用的函数，根据 node_id 获取当前 PromptSelectorNode 实例
    """
    global prompt_selector_nodes

    if node_id not in prompt_selector_nodes:
        prompt_selector_nodes[node_id] = PromptSelectorNode()

    return prompt_selector_nodes[node_id]
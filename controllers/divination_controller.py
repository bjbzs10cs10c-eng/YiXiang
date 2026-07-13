"""占卜控制器 - 连接UI层与服务层"""

from services.divination_service import start_divination, save_record
from services.history_service import save_record as history_save


class DivinationController:
    """占卜控制器，UI层通过此控制器调用服务层"""

    def perform_divination(self, question: str) -> dict:
        """执行完整占卜流程

        Args:
            question: 占问事项

        Returns:
            完整占卜结果
        """
        if not question or not question.strip():
            raise ValueError("请输入占问事项")
        return start_divination(question.strip())

    def save_result(self, result: dict) -> int:
        """保存占卜结果到历史记录

        Args:
            result: perform_divination返回的结果

        Returns:
            记录ID
        """
        original_id = result["original_hexagram"]["id"]
        changed_id = result["changed_hexagram"]["id"] if result["changed_hexagram"] else None

        return history_save(
            question=result["question"],
            original_id=original_id,
            changed_id=changed_id,
            moving_lines=result["moving_lines"],
            yao_values=result["tosses"],
            create_time=result["time"],
        )

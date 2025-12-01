from typing import List, Dict, Any
from statistics import mean

class TrendAnalyzer:
    def __init__(self, data_points: Dict[str, float]):
        """
        data_points: دیکشنری از {بازه زمانی: مقدار}
        """
        self.data_points = data_points

    def average_value(self) -> float:
        if not self.data_points:
            return 0.0
        return round(mean(self.data_points.values()), 2)

    def trend_direction(self) -> str:
        if not self.data_points or len(self.data_points) < 2:
            return "No trend"
        values = list(self.data_points.values())
        if values[-1] > values[0]:
            return "Upward"
        elif values[-1] < values[0]:
            return "Downward"
        else:
            return "Stable"

    def max_value(self) -> float:
        if not self.data_points:
            return 0.0
        return max(self.data_points.values())

    def min_value(self) -> float:
        if not self.data_points:
            return 0.0
        return min(self.data_points.values())

    def render_text_analysis(self) -> str:
        avg = self.average_value()
        trend = self.trend_direction()
        max_val = self.max_value()
        min_val = self.min_value()
        lines = []
        lines.append("Trend Analysis Report")
        lines.append("=" * 40)
        lines.append(f"Average Value: {avg}")
        lines.append(f"Trend Direction: {trend}")
        lines.append(f"Max Value: {max_val}")
        lines.append(f"Min Value: {min_val}")
        return "\n".join(lines)

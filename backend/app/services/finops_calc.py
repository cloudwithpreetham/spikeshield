from app.models.finops import EnvironmentCost, InstanceCost
from datetime import datetime

class FinOpsCalculator:
    PRICES = {
        "t3.micro": 0.0104, "t3.small": 0.0208, "t3.medium": 0.0416, "t3.large": 0.0832,
        "t3.xlarge": 0.1664, "m5.large": 0.096, "m5.xlarge": 0.192, "c5.large": 0.085, "c5.xlarge": 0.17
    }

    def calculate_environment_cost(self, instances_info: list, request_count_per_hour: int = 150000, env_name: str = "spikeshield-prod") -> EnvironmentCost:
        instances = []
        for info in instances_info:
            inst_type = info.get("instance_type") or info.get("type", "t3.micro")
            is_spot = info.get("is_spot", False)
            price = self.PRICES.get(inst_type, 0.0104)
            if is_spot:
                price = price * self.get_spot_discount_factor(inst_type)
            count = info.get("count", 1)
            cost = price * count * 84.0
            instances.append(InstanceCost(
                instance_type=inst_type,
                count=count,
                hourly_rate_usd=price,
                is_spot=is_spot,
                hourly_cost_inr=round(cost, 2)
            ))
        
        total_hourly = sum(i.hourly_cost_inr for i in instances)
        total_daily = total_hourly * 24
        
        # Unit economics: INR per 10k requests
        cost_per_10k = (total_hourly / (request_count_per_hour / 10000.0)) if request_count_per_hour > 0 else 0.0

        return EnvironmentCost(
            env_name=env_name,
            instances=instances,
            total_hourly_inr=round(total_hourly, 2),
            total_daily_inr=round(total_daily, 2),
            cost_per_10k_requests=round(cost_per_10k, 2),
            computed_at=datetime.utcnow()
        )

    def get_spot_discount_factor(self, instance_type: str) -> float:
        return 0.3

    def format_inr(self, amount: float) -> str:
        return f"₹{amount:,.2f}"

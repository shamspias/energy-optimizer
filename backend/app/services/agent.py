from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Dict, Any, Optional
import json
from app.config import settings
from app.db.memory import MemoryStore


class EnergyAdvisorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4.1",
            temperature=0.7
        ) if settings.openai_api_key else None
        self.memory_store = MemoryStore()

    async def advise(
            self,
            user_id: str,
            optimization_result: Dict[str, Any],
            context: Optional[str] = None,
            zone_eic: str = None,
            date_str: str = None
    ) -> Dict[str, Any]:
        """Generate advice based on optimization results and user context"""

        if not self.llm:
            # Return a mock response if no OpenAI key
            return self._generate_mock_advice(optimization_result)

        # Retrieve user preferences from memory
        user_prefs = await self.memory_store.get_user_preferences(user_id)

        # Build prompt
        system_prompt = """You are an expert energy advisor helping users optimize their electricity consumption.
        Analyze the optimization results and provide clear, actionable advice.
        Consider user preferences and context when making recommendations.
        Be specific about savings and timing."""

        human_prompt = f"""
        Optimization Results:
        - Baseline Cost: €{optimization_result['baseline_cost_eur']}
        - Optimized Cost: €{optimization_result['optimized_cost_eur']}
        - Savings: €{optimization_result['savings_eur']} ({optimization_result['savings_percent']}%)

        Schedule:
        {json.dumps([{
            'hour': str(s.hour_utc),
            'kwh': s.shift_kwh,
            'price': s.price_eur_kwh
        } for s in optimization_result['schedule']], indent=2)}

        User Preferences: {user_prefs}
        Additional Context: {context or 'None provided'}

        Provide:
        1. A concise recommendation (2-3 sentences)
        2. Key reasoning points
        3. Any warnings or considerations
        """

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ])

            advice_text = response.content

            # Parse structured response
            reasoning = self._extract_reasoning(advice_text)

            return {
                'advice': advice_text[:200],  # First part as summary
                'reasoning': reasoning,
                'plan': {
                    'savings': optimization_result['savings_eur'],
                    'best_hours': [str(s.hour_utc) for s in optimization_result['schedule'][:3]],
                    'action': 'shift_load'
                },
                'confidence': 0.85
            }

        except Exception as e:
            print(f"Agent error: {e}")
            return self._generate_mock_advice(optimization_result)

    def _extract_reasoning(self, text: str) -> str:
        """Extract reasoning from LLM response"""
        # Simple extraction - in production, use better parsing
        lines = text.split('\n')
        reasoning = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['because', 'since', 'due to', 'based on']):
                reasoning.append(line.strip())
        return ' '.join(reasoning[:3]) if reasoning else "Based on price analysis."

    def _generate_mock_advice(self, optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock advice when LLM is not available"""
        schedule = optimization_result['schedule']
        best_hours = schedule[:3] if len(schedule) >= 3 else schedule

        hour_ranges = []
        for hour in best_hours:
            hour_ranges.append(f"{hour.hour_utc.strftime('%H:%M')}")

        advice = f"Shift your flexible load to {', '.join(hour_ranges)} UTC to save €{optimization_result['savings_eur']}. These are the cheapest hours today."

        reasoning = f"Prices are lowest during overnight hours. By shifting {sum(h.shift_kwh for h in schedule)} kWh to these periods, you'll save {optimization_result['savings_percent']}% on your flexible consumption."

        return {
            'advice': advice,
            'reasoning': reasoning,
            'plan': {
                'savings': optimization_result['savings_eur'],
                'best_hours': [str(h.hour_utc) for h in best_hours],
                'action': 'shift_load'
            },
            'confidence': 0.85
        }

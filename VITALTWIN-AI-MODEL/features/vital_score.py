# features/vital_score.py

class VitalScoreGauge:
    """
    Feature 8: Unified Vital Score (0-100)
    Quick health snapshot with visual gauge
    """
    
    def __init__(self):
        self.thresholds = {
            'green': [80, 100],
            'yellow': [50, 79],
            'red': [0, 49]
        }
    
    def calculate(self, overall_health_score, trend_data=None):
        """
        Create vital score with gauge visualization
        
        Args:
            overall_health_score: Current health score (0-100)
            trend_data: Historical scores for trend
        
        Returns:
            Vital score with gauge data
        """
        # Determine category
        if overall_health_score >= 80:
            category = "Excellent"
            color = "GREEN"
            message = "✅ Your health is excellent! Keep it up!"
        elif overall_health_score >= 60:
            category = "Good"
            color = "GREEN"
            message = "✅ Good health, room for improvement"
        elif overall_health_score >= 40:
            category = "Fair"
            color = "YELLOW"
            message = "⚠️ Moderate health concerns to address"
        elif overall_health_score >= 20:
            category = "Poor"
            color = "RED"
            message = "🔴 Significant health risks detected"
        else:
            category = "Critical"
            color = "RED"
            message = "🔴 CRITICAL: Immediate action needed"
        
        # Calculate trend
        trend = self._calculate_trend(trend_data) if trend_data else "stable"
        trend_percent = self._calculate_trend_percent(trend_data) if trend_data else 0
        
        # Create gauge data for frontend
        gauge = {
            'value': overall_health_score,
            'min': 0,
            'max': 100,
            'segments': [
                {'from': 0, 'to': 49, 'color': '#F44336', 'label': 'Critical'},
                {'from': 50, 'to': 79, 'color': '#FFC107', 'label': 'Fair'},
                {'from': 80, 'to': 100, 'color': '#4CAF50', 'label': 'Good'}
            ],
            'current_segment': self._get_current_segment(overall_health_score),
            'needle': {
                'value': overall_health_score,
                'color': '#333333'
            }
        }
        
        return {
            'current': overall_health_score,
            'category': category,
            'color': color,
            'message': message,
            'trend': trend,
            'trend_percent': trend_percent,
            'gauge': gauge,
            'interpretation': self._get_interpretation(overall_health_score)
        }
    
    def _calculate_trend(self, trend_data):
        """Calculate health trend"""
        if len(trend_data) < 2:
            return "stable"
        
        first = trend_data[0]
        last = trend_data[-1]
        
        if last > first + 5:
            return "improving"
        elif last < first - 5:
            return "declining"
        else:
            return "stable"
    
    def _calculate_trend_percent(self, trend_data):
        """Calculate trend percentage"""
        if len(trend_data) < 2:
            return 0
        
        first = trend_data[0]
        last = trend_data[-1]
        
        if first == 0:
            return 0
        
        return round(((last - first) / first) * 100, 1)
    
    def _get_current_segment(self, score):
        """Get current gauge segment"""
        if score >= 80:
            return {'color': '#4CAF50', 'label': 'Good'}
        elif score >= 50:
            return {'color': '#FFC107', 'label': 'Fair'}
        else:
            return {'color': '#F44336', 'label': 'Critical'}
    
    def _get_interpretation(self, score):
        """Get detailed interpretation"""
        if score >= 80:
            return "Your vital signs are excellent. Maintain your healthy habits."
        elif score >= 60:
            return "You're doing well, but there's room for improvement in a few areas."
        elif score >= 40:
            return "Several health markers need attention. Focus on lifestyle changes."
        elif score >= 20:
            return "Significant health risks detected. Consult healthcare providers."
        else:
            return "Critical health status. Immediate medical attention recommended."
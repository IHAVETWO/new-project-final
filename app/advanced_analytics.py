import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional, Any
from .models import db, User, Appointment, MedicalRecord, DentalHistory, Service, Notification
import json
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

class AdvancedAnalytics:
    """Advanced analytics with machine learning capabilities"""
    
    def __init__(self):
        self.colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d', '#17a2b8', '#6f42c1', '#fd7e14']
        self.models = {}
        self.scalers = {}
        
    def prepare_appointment_data(self, days: int = 365) -> pd.DataFrame:
        """Prepare appointment data for ML analysis"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        appointments = Appointment.query.filter(
            Appointment.date >= start_date,
            Appointment.date <= end_date,
            Appointment.is_deleted == False
        ).all()
        
        data = []
        for apt in appointments:
            data.append({
                'date': apt.date,
                'day_of_week': apt.date.weekday(),
                'month': apt.date.month,
                'year': apt.date.year,
                'hour': apt.time.hour,
                'service_type': apt.service_type,
                'duration': apt.duration,
                'status': apt.status,
                'user_id': apt.user_id
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['is_weekend'] = df['day_of_week'].isin([5, 6])
            df['is_holiday'] = self._is_holiday(df['date'])
            df['season'] = df['month'].apply(self._get_season)
        
        return df
    
    def _is_holiday(self, dates: pd.Series) -> pd.Series:
        """Check if dates are holidays (simplified)"""
        # Major US holidays
        holidays = [
            '2024-01-01', '2024-01-15', '2024-02-19', '2024-05-27', '2024-07-04',
            '2024-09-02', '2024-10-14', '2024-11-11', '2024-11-28', '2024-12-25'
        ]
        return dates.dt.strftime('%Y-%m-%d').isin(holidays)
    
    def _get_season(self, month: int) -> str:
        """Get season from month"""
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
    
    def predict_appointment_demand_ml(self, days_ahead: int = 30) -> Dict:
        """Predict appointment demand using machine learning"""
        df = self.prepare_appointment_data()
        
        if df.empty:
            return {
                'predictions': [0] * days_ahead,
                'confidence_level': 'low',
                'method': 'no_data',
                'error': 'Insufficient data for prediction'
            }
        
        # Aggregate daily appointments
        daily_counts = df.groupby('date').size().reset_index(name='appointments')
        daily_counts['day_of_week'] = daily_counts['date'].dt.weekday
        daily_counts['month'] = daily_counts['date'].dt.month
        daily_counts['is_weekend'] = daily_counts['day_of_week'].isin([5, 6])
        
        # Create features
        daily_counts['lag_1'] = daily_counts['appointments'].shift(1)
        daily_counts['lag_7'] = daily_counts['appointments'].shift(7)
        daily_counts['rolling_mean_7'] = daily_counts['appointments'].rolling(7).mean()
        daily_counts['rolling_std_7'] = daily_counts['appointments'].rolling(7).std()
        
        # Drop NaN values
        daily_counts = daily_counts.dropna()
        
        if len(daily_counts) < 30:
            return {
                'predictions': [daily_counts['appointments'].mean()] * days_ahead,
                'confidence_level': 'low',
                'method': 'simple_average',
                'error': 'Insufficient data for ML prediction'
            }
        
        # Prepare features and target
        features = ['day_of_week', 'month', 'is_weekend', 'lag_1', 'lag_7', 'rolling_mean_7', 'rolling_std_7']
        X = daily_counts[features]
        y = daily_counts['appointments']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Generate predictions
        last_date = daily_counts['date'].max()
        predictions = []
        
        for i in range(days_ahead):
            pred_date = last_date + timedelta(days=i+1)
            
            # Create feature vector for prediction
            pred_features = pd.DataFrame([{
                'day_of_week': pred_date.weekday(),
                'month': pred_date.month,
                'is_weekend': pred_date.weekday() in [5, 6],
                'lag_1': daily_counts['appointments'].iloc[-1] if i == 0 else predictions[-1],
                'lag_7': daily_counts['appointments'].iloc[-7] if len(daily_counts) >= 7 else daily_counts['appointments'].mean(),
                'rolling_mean_7': daily_counts['appointments'].tail(7).mean(),
                'rolling_std_7': daily_counts['appointments'].tail(7).std()
            }])
            
            pred = model.predict(pred_features)[0]
            predictions.append(max(0, round(pred)))
        
        confidence_level = 'high' if r2 > 0.7 else 'medium' if r2 > 0.5 else 'low'
        
        return {
            'predictions': predictions,
            'confidence_level': confidence_level,
            'method': 'random_forest',
            'model_score': r2,
            'mse': mse,
            'feature_importance': dict(zip(features, model.feature_importances_))
        }
    
    def analyze_patient_behavior(self) -> Dict:
        """Analyze patient behavior patterns"""
        users = User.query.filter(User.is_deleted == False).all()
        appointments = Appointment.query.filter(Appointment.is_deleted == False).all()
        
        # Patient engagement analysis
        engagement_data = []
        for user in users:
            user_appointments = [apt for apt in appointments if apt.user_id == user.id]
            
            if user_appointments:
                first_apt = min(user_appointments, key=lambda x: x.date)
                last_apt = max(user_appointments, key=lambda x: x.date)
                total_apts = len(user_appointments)
                completed_apts = len([apt for apt in user_appointments if apt.status == 'completed'])
                cancelled_apts = len([apt for apt in user_appointments if apt.status == 'cancelled'])
                
                engagement_data.append({
                    'user_id': user.id,
                    'total_appointments': total_apts,
                    'completed_appointments': completed_apts,
                    'cancelled_appointments': cancelled_apts,
                    'completion_rate': completed_apts / total_apts if total_apts > 0 else 0,
                    'days_since_last_visit': (date.today() - last_apt.date).days,
                    'avg_days_between_visits': (last_apt.date - first_apt.date).days / (total_apts - 1) if total_apts > 1 else 0
                })
        
        if not engagement_data:
            return {'error': 'No appointment data available'}
        
        df = pd.DataFrame(engagement_data)
        
        # Segment patients
        df['engagement_segment'] = pd.cut(df['completion_rate'], 
                                        bins=[0, 0.5, 0.8, 1.0], 
                                        labels=['Low', 'Medium', 'High'])
        
        df['frequency_segment'] = pd.cut(df['total_appointments'], 
                                       bins=[0, 2, 5, 10, 100], 
                                       labels=['New', 'Occasional', 'Regular', 'Frequent'])
        
        return {
            'total_patients': len(users),
            'active_patients': len([u for u in users if any(apt.status == 'completed' for apt in appointments if apt.user_id == u.id)]),
            'engagement_segments': df['engagement_segment'].value_counts().to_dict(),
            'frequency_segments': df['frequency_segment'].value_counts().to_dict(),
            'avg_completion_rate': df['completion_rate'].mean(),
            'avg_appointments_per_patient': df['total_appointments'].mean(),
            'patient_retention_rate': len(df[df['total_appointments'] > 1]) / len(df) if len(df) > 0 else 0,
            'risk_patients': len(df[df['days_since_last_visit'] > 365])
        }
    
    def predict_patient_churn(self) -> Dict:
        """Predict which patients are likely to churn"""
        users = User.query.filter(User.is_deleted == False).all()
        appointments = Appointment.query.filter(Appointment.is_deleted == False).all()
        
        churn_data = []
        for user in users:
            user_appointments = [apt for apt in appointments if apt.user_id == user.id]
            
            if user_appointments:
                last_apt = max(user_appointments, key=lambda x: x.date)
                days_since_last = (date.today() - last_apt.date).days
                total_apts = len(user_appointments)
                cancelled_rate = len([apt for apt in user_appointments if apt.status == 'cancelled']) / total_apts
                
                # Churn probability based on behavior patterns
                churn_prob = 0
                if days_since_last > 365:
                    churn_prob += 0.4
                if cancelled_rate > 0.5:
                    churn_prob += 0.3
                if total_apts < 2:
                    churn_prob += 0.2
                if days_since_last > 180:
                    churn_prob += 0.1
                
                churn_data.append({
                    'user_id': user.id,
                    'days_since_last_visit': days_since_last,
                    'total_appointments': total_apts,
                    'cancellation_rate': cancelled_rate,
                    'churn_probability': min(1.0, churn_prob),
                    'risk_level': 'High' if churn_prob > 0.6 else 'Medium' if churn_prob > 0.3 else 'Low'
                })
        
        if not churn_data:
            return {'error': 'No data available for churn analysis'}
        
        df = pd.DataFrame(churn_data)
        
        return {
            'high_risk_patients': len(df[df['risk_level'] == 'High']),
            'medium_risk_patients': len(df[df['risk_level'] == 'Medium']),
            'low_risk_patients': len(df[df['risk_level'] == 'Low']),
            'avg_churn_probability': df['churn_probability'].mean(),
            'patients_needing_attention': df[df['churn_probability'] > 0.5].to_dict('records')
        }
    
    def optimize_scheduling(self) -> Dict:
        """Optimize appointment scheduling based on patterns"""
        df = self.prepare_appointment_data()
        
        if df.empty:
            return {'error': 'No appointment data available'}
        
        # Analyze peak hours
        hourly_distribution = df.groupby('hour').size().to_dict()
        
        # Analyze day of week patterns
        daily_distribution = df.groupby('day_of_week').size().to_dict()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_distribution_named = {day_names[i]: count for i, count in daily_distribution.items()}
        
        # Analyze seasonal patterns
        seasonal_distribution = df.groupby('season').size().to_dict()
        
        # Find optimal scheduling slots
        peak_hours = sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_days = sorted(daily_distribution_named.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Calculate capacity utilization
        total_slots = len(df) * 60  # Assuming 60-minute slots
        total_duration = df['duration'].sum()
        utilization_rate = total_duration / total_slots if total_slots > 0 else 0
        
        return {
            'peak_hours': [{'hour': hour, 'appointments': count} for hour, count in peak_hours],
            'peak_days': [{'day': day, 'appointments': count} for day, count in peak_days],
            'seasonal_patterns': seasonal_distribution,
            'capacity_utilization': utilization_rate,
            'recommendations': self._generate_scheduling_recommendations(df)
        }
    
    def _generate_scheduling_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate scheduling recommendations based on data"""
        recommendations = []
        
        # Analyze patterns and generate recommendations
        if len(df) > 0:
            avg_daily = df.groupby('date').size().mean()
            if avg_daily > 20:
                recommendations.append("Consider adding more appointment slots during peak hours")
            
            weekend_apts = df[df['is_weekend'] == True]
            if len(weekend_apts) > len(df) * 0.3:
                recommendations.append("High weekend demand - consider extending weekend hours")
            
            cancelled_rate = len(df[df['status'] == 'cancelled']) / len(df)
            if cancelled_rate > 0.2:
                recommendations.append("High cancellation rate - implement reminder system")
        
        return recommendations
    
    def generate_business_insights(self) -> Dict:
        """Generate comprehensive business insights"""
        # Get all analytics
        demand_prediction = self.predict_appointment_demand_ml()
        patient_behavior = self.analyze_patient_behavior()
        churn_analysis = self.predict_patient_churn()
        scheduling_optimization = self.optimize_scheduling()
        
        # Calculate key metrics
        total_revenue = self._calculate_total_revenue()
        growth_rate = self._calculate_growth_rate()
        
        insights = {
            'demand_forecast': demand_prediction,
            'patient_behavior': patient_behavior,
            'churn_analysis': churn_analysis,
            'scheduling_optimization': scheduling_optimization,
            'financial_metrics': {
                'total_revenue': total_revenue,
                'growth_rate': growth_rate,
                'avg_revenue_per_patient': total_revenue / patient_behavior.get('active_patients', 1)
            },
            'strategic_recommendations': self._generate_strategic_recommendations(
                demand_prediction, patient_behavior, churn_analysis
            )
        }
        
        return insights
    
    def _calculate_total_revenue(self) -> float:
        """Calculate total revenue from appointments"""
        appointments = Appointment.query.filter(
            Appointment.status == 'completed',
            Appointment.is_deleted == False
        ).all()
        
        total = 0
        for apt in appointments:
            if apt.cost:
                total += apt.cost
            else:
                # Estimate cost based on service type
                service = Service.query.filter_by(name=apt.service_type).first()
                if service and service.base_cost:
                    total += service.base_cost
        
        return total
    
    def _calculate_growth_rate(self) -> float:
        """Calculate month-over-month growth rate"""
        current_month = date.today().replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        current_month_apts = Appointment.query.filter(
            Appointment.date >= current_month,
            Appointment.is_deleted == False
        ).count()
        
        last_month_apts = Appointment.query.filter(
            Appointment.date >= last_month,
            Appointment.date < current_month,
            Appointment.is_deleted == False
        ).count()
        
        if last_month_apts > 0:
            return ((current_month_apts - last_month_apts) / last_month_apts) * 100
        return 0
    
    def _generate_strategic_recommendations(self, demand_pred, behavior, churn) -> List[str]:
        """Generate strategic business recommendations"""
        recommendations = []
        
        # Based on demand prediction
        if demand_pred.get('confidence_level') == 'high':
            avg_predicted = np.mean(demand_pred.get('predictions', [0]))
            if avg_predicted > 15:
                recommendations.append("High predicted demand - consider hiring additional staff")
            elif avg_predicted < 5:
                recommendations.append("Low predicted demand - focus on marketing campaigns")
        
        # Based on patient behavior
        if behavior.get('avg_completion_rate', 0) < 0.8:
            recommendations.append("Low appointment completion rate - improve patient communication")
        
        if behavior.get('risk_patients', 0) > 10:
            recommendations.append("Many inactive patients - implement re-engagement campaign")
        
        # Based on churn analysis
        if churn.get('high_risk_patients', 0) > 5:
            recommendations.append("High churn risk - implement retention strategies")
        
        return recommendations
    
    def create_advanced_visualizations(self) -> Dict:
        """Create advanced data visualizations"""
        df = self.prepare_appointment_data()
        
        if df.empty:
            return {'error': 'No data available for visualization'}
        
        visualizations = {}
        
        # Time series plot
        daily_counts = df.groupby('date').size()
        plt.figure(figsize=(12, 6))
        daily_counts.plot(kind='line', color=self.colors[0])
        plt.title('Appointment Trends Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Appointments')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        visualizations['time_series'] = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        # Heatmap of appointments by day and hour
        pivot_table = df.pivot_table(index='day_of_week', columns='hour', values='id', aggfunc='count', fill_value=0)
        plt.figure(figsize=(12, 8))
        sns.heatmap(pivot_table, annot=True, fmt='d', cmap='YlOrRd')
        plt.title('Appointment Heatmap: Day vs Hour')
        plt.xlabel('Hour of Day')
        plt.ylabel('Day of Week')
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        visualizations['heatmap'] = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return visualizations

# Initialize the advanced analytics
advanced_analytics = AdvancedAnalytics() 
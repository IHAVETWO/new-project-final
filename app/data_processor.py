import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional
from .models import db, User, Appointment, MedicalRecord, DentalHistory, Service, Notification
import json
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

class DataProcessor:
    """Advanced data processing and analytics for dental clinic"""
    
    def __init__(self):
        self.colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d', '#17a2b8']
    
    def get_appointment_trends(self, days: int = 30) -> Dict:
        """Analyze appointment trends over time"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get appointments in date range
        appointments = Appointment.query.filter(
            Appointment.date >= start_date,
            Appointment.date <= end_date
        ).all()
        
        # Create daily counts
        daily_counts = {}
        current_date = start_date
        while current_date <= end_date:
            daily_counts[current_date] = 0
            current_date += timedelta(days=1)
        
        for apt in appointments:
            if apt.date in daily_counts:
                daily_counts[apt.date] += 1
        
        # Calculate trends
        dates = list(daily_counts.keys())
        counts = list(daily_counts.values())
        
        # Simple moving average
        window = 7
        moving_avg = []
        for i in range(len(counts)):
            if i < window - 1:
                moving_avg.append(np.mean(counts[:i+1]))
            else:
                moving_avg.append(np.mean(counts[i-window+1:i+1]))
        
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'counts': counts,
            'moving_average': moving_avg,
            'total_appointments': sum(counts),
            'average_daily': np.mean(counts),
            'peak_day': dates[counts.index(max(counts))].strftime('%Y-%m-%d'),
            'peak_count': max(counts)
        }
    
    def analyze_user_demographics(self) -> Dict:
        """Analyze user demographics and patterns"""
        users = User.query.all()
        
        # Age distribution
        ages = []
        for user in users:
            if user.date_of_birth:
                age = user.get_age()
                if age:
                    ages.append(age)
        
        age_groups = {
            '18-25': len([a for a in ages if 18 <= a <= 25]),
            '26-35': len([a for a in ages if 26 <= a <= 35]),
            '36-45': len([a for a in ages if 36 <= a <= 45]),
            '46-55': len([a for a in ages if 46 <= a <= 55]),
            '56-65': len([a for a in ages if 56 <= a <= 65]),
            '65+': len([a for a in ages if a > 65])
        }
        
        # Gender distribution (if available)
        demographics = {
            'Male': len([u for u in users if getattr(u, 'gender', None) == 'male']),
            'Female': len([u for u in users if getattr(u, 'gender', None) == 'female']),
            'Unspecified': len([u for u in users if not getattr(u, 'gender', None) or getattr(u, 'gender', None) not in ['male', 'female']])
        }
        
        # Registration trends
        registration_dates = [u.created_at.date() for u in users if u.created_at]
        monthly_registrations = {}
        
        for reg_date in registration_dates:
            month_key = reg_date.strftime('%Y-%m')
            monthly_registrations[month_key] = monthly_registrations.get(month_key, 0) + 1
        
        return {
            'total_users': len(users),
            'age_distribution': age_groups,
            'gender_distribution': demographics,
            'monthly_registrations': monthly_registrations,
            'average_age': np.mean(ages) if ages else 0,
            'median_age': np.median(ages) if ages else 0
        }
    
    def service_analysis(self) -> Dict:
        """Analyze service patterns and profitability"""
        services = Service.query.all()
        appointments = Appointment.query.all()
        
        service_stats = {}
        for service in services:
            service_appointments = [apt for apt in appointments if apt.service_type == service.name]
            
            service_stats[service.name] = {
                'total_appointments': len(service_appointments),
                'completed': len([apt for apt in service_appointments if apt.status == 'completed']),
                'cancelled': len([apt for apt in service_appointments if apt.status == 'cancelled']),
                'average_duration': service.duration or 60,
                'base_cost': service.base_cost or 0,
                'category': service.category,
                'completion_rate': len([apt for apt in service_appointments if apt.status == 'completed']) / len(service_appointments) * 100 if service_appointments else 0
            }
        
        # Calculate revenue by service
        dental_records = DentalHistory.query.all()
        revenue_by_service = {}
        
        for record in dental_records:
            service_name = record.procedure_type
            if service_name not in revenue_by_service:
                revenue_by_service[service_name] = 0
            revenue_by_service[service_name] += record.cost or 0
        
        # Add revenue to service stats
        for service_name, revenue in revenue_by_service.items():
            if service_name in service_stats:
                service_stats[service_name]['total_revenue'] = revenue
                service_stats[service_name]['average_revenue_per_appointment'] = revenue / service_stats[service_name]['total_appointments'] if service_stats[service_name]['total_appointments'] > 0 else 0
        
        return {
            'service_statistics': service_stats,
            'most_popular_service': max(service_stats.items(), key=lambda x: x[1]['total_appointments'])[0] if service_stats else None,
            'most_profitable_service': max(service_stats.items(), key=lambda x: x[1].get('total_revenue', 0))[0] if service_stats else None,
            'total_services': len(services)
        }
    
    def predict_appointment_demand(self, days_ahead: int = 30) -> Dict:
        """Predict appointment demand using simple forecasting"""
        # Get historical data
        end_date = date.today()
        start_date = end_date - timedelta(days=90)  # 3 months of data
        
        appointments = Appointment.query.filter(
            Appointment.date >= start_date,
            Appointment.date <= end_date
        ).all()
        
        # Create daily appointment counts
        daily_counts = {}
        current_date = start_date
        while current_date <= end_date:
            daily_counts[current_date] = 0
            current_date += timedelta(days=1)
        
        for apt in appointments:
            if apt.date in daily_counts:
                daily_counts[apt.date] += 1
        
        counts = list(daily_counts.values())
        
        # Simple forecasting using moving average and trend
        if len(counts) >= 7:
            # Calculate trend
            recent_avg = np.mean(counts[-7:])
            older_avg = np.mean(counts[-14:-7])
            trend = (recent_avg - older_avg) / 7
            
            # Predict future values
            predictions = []
            for i in range(days_ahead):
                predicted = recent_avg + (trend * (i + 1))
                predictions.append(max(0, predicted))  # Ensure non-negative
            
            return {
                'predictions': predictions,
                'confidence_level': 'medium',
                'method': 'moving_average_with_trend',
                'current_average': recent_avg,
                'trend_direction': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable'
            }
        else:
            # Not enough data for prediction
            return {
                'predictions': [np.mean(counts)] * days_ahead if counts else [0] * days_ahead,
                'confidence_level': 'low',
                'method': 'simple_average',
                'current_average': np.mean(counts) if counts else 0,
                'trend_direction': 'unknown'
            }
    
    def generate_health_insights(self) -> Dict:
        """Generate insights about patient health patterns"""
        medical_records = MedicalRecord.query.all()
        dental_history = DentalHistory.query.all()
        
        # Analyze common medical conditions
        conditions = {}
        for record in medical_records:
            if record.record_type == 'medical':
                condition = record.title.lower()
                conditions[condition] = conditions.get(condition, 0) + 1
        
        # Analyze dental procedures
        procedures = {}
        for record in dental_history:
            procedure = record.procedure_type.lower()
            procedures[procedure] = procedures.get(procedure, 0) + 1
        
        # Find correlations between conditions and procedures
        correlations = {}
        for user in User.query.all():
            user_conditions = [r.title.lower() for r in medical_records if r.user_id == user.id and r.record_type == 'medical']
            user_procedures = [r.procedure_type.lower() for r in dental_history if r.user_id == user.id]
            
            for condition in user_conditions:
                for procedure in user_procedures:
                    key = f"{condition} -> {procedure}"
                    correlations[key] = correlations.get(key, 0) + 1
        
        return {
            'common_conditions': dict(sorted(conditions.items(), key=lambda x: x[1], reverse=True)[:10]),
            'common_procedures': dict(sorted(procedures.items(), key=lambda x: x[1], reverse=True)[:10]),
            'condition_procedure_correlations': dict(sorted(correlations.items(), key=lambda x: x[1], reverse=True)[:10]),
            'total_medical_records': len(medical_records),
            'total_dental_procedures': len(dental_history)
        }
    
    def create_performance_report(self) -> Dict:
        """Create comprehensive performance report"""
        # Get all the analytics
        appointment_trends = self.get_appointment_trends()
        demographics = self.analyze_user_demographics()
        service_analysis = self.service_analysis()
        demand_prediction = self.predict_appointment_demand()
        health_insights = self.generate_health_insights()
        
        # Calculate KPIs
        total_revenue = sum(service['total_revenue'] for service in service_analysis['service_statistics'].values() if 'total_revenue' in service)
        total_appointments = sum(service['total_appointments'] for service in service_analysis['service_statistics'].values())
        completion_rate = sum(service['completed'] for service in service_analysis['service_statistics'].values()) / total_appointments * 100 if total_appointments > 0 else 0
        
        return {
            'report_date': date.today().isoformat(),
            'kpis': {
                'total_revenue': total_revenue,
                'total_appointments': total_appointments,
                'completion_rate': completion_rate,
                'total_users': demographics['total_users'],
                'average_daily_appointments': appointment_trends['average_daily']
            },
            'appointment_trends': appointment_trends,
            'demographics': demographics,
            'service_analysis': service_analysis,
            'demand_prediction': demand_prediction,
            'health_insights': health_insights,
            'recommendations': self.generate_recommendations()
        }
    
    def generate_recommendations(self) -> List[str]:
        """Generate business recommendations based on data analysis"""
        recommendations = []
        
        # Analyze appointment trends
        trends = self.get_appointment_trends()
        if trends['average_daily'] < 5:
            recommendations.append("Consider implementing marketing campaigns to increase appointment bookings")
        
        # Analyze service popularity
        service_analysis = self.service_analysis()
        if service_analysis['service_statistics']:
            most_popular = service_analysis['most_popular_service']
            least_popular = min(service_analysis['service_statistics'].items(), key=lambda x: x[1]['total_appointments'])[0]
            
            recommendations.append(f"Focus on promoting {least_popular} services to increase utilization")
            recommendations.append(f"Leverage the popularity of {most_popular} services for cross-selling")
        
        # Analyze completion rates
        low_completion_services = [name for name, stats in service_analysis['service_statistics'].items() if stats['completion_rate'] < 70]
        if low_completion_services:
            recommendations.append(f"Investigate reasons for low completion rates in: {', '.join(low_completion_services)}")
        
        # Analyze demographics
        demographics = self.analyze_user_demographics()
        if demographics['average_age'] > 50:
            recommendations.append("Consider services and marketing targeted at younger demographics")
        
        return recommendations
    
    def export_to_excel(self, report_data: Dict) -> BytesIO:
        """Export report data to Excel format"""
        # Create Excel writer
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # KPI Summary
            kpi_df = pd.DataFrame([report_data['kpis']])
            kpi_df.to_excel(writer, sheet_name='KPI Summary', index=False)
            
            # Appointment Trends
            trends_df = pd.DataFrame({
                'Date': report_data['appointment_trends']['dates'],
                'Appointments': report_data['appointment_trends']['counts'],
                'Moving Average': report_data['appointment_trends']['moving_average']
            })
            trends_df.to_excel(writer, sheet_name='Appointment Trends', index=False)
            
            # Service Analysis
            service_data = []
            for service_name, stats in report_data['service_analysis']['service_statistics'].items():
                service_data.append({
                    'Service': service_name,
                    'Total Appointments': stats['total_appointments'],
                    'Completed': stats['completed'],
                    'Cancelled': stats['cancelled'],
                    'Completion Rate (%)': stats['completion_rate'],
                    'Total Revenue': stats.get('total_revenue', 0),
                    'Category': stats['category']
                })
            service_df = pd.DataFrame(service_data)
            service_df.to_excel(writer, sheet_name='Service Analysis', index=False)
            
            # Demographics
            demo_data = []
            for age_group, count in report_data['demographics']['age_distribution'].items():
                demo_data.append({'Age Group': age_group, 'Count': count})
            demo_df = pd.DataFrame(demo_data)
            demo_df.to_excel(writer, sheet_name='Demographics', index=False)
        
        output.seek(0)
        return output
    
    def create_visualization(self, data_type: str, data: Dict) -> str:
        """Create data visualizations and return as base64 encoded image"""
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if data_type == 'appointment_trends':
            dates = [datetime.strptime(d, '%Y-%m-%d') for d in data['dates']]
            ax.plot(dates, data['counts'], label='Daily Appointments', color='#007bff', alpha=0.7)
            ax.plot(dates, data['moving_average'], label='7-Day Moving Average', color='#28a745', linewidth=2)
            ax.set_title('Appointment Trends (Last 30 Days)')
            ax.set_xlabel('Date')
            ax.set_ylabel('Number of Appointments')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        elif data_type == 'service_popularity':
            services = list(data.keys())
            counts = list(data.values())
            bars = ax.bar(services, counts, color=self.colors[:len(services)])
            ax.set_title('Service Popularity')
            ax.set_xlabel('Service')
            ax.set_ylabel('Number of Appointments')
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                       str(count), ha='center', va='bottom')
        
        elif data_type == 'age_distribution':
            age_groups = list(data.keys())
            counts = list(data.values())
            ax.pie(counts, labels=age_groups, autopct='%1.1f%%', colors=self.colors[:len(age_groups)])
            ax.set_title('Age Distribution')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode()

# Initialize global instance
data_processor = DataProcessor() 
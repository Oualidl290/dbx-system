import pandas as pd
import numpy as np
from typing import Dict, List, Any
import google.generativeai as genai
from datetime import datetime
import json
import logging
import os
from ..config import settings

class ReportGenerator:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
    
    async def generate_report(self, 
                            log_data: pd.DataFrame, 
                            risk_score: float = None, 
                            anomalies: List[Dict] = None, 
                            shap_values: Dict = None,
                            comprehensive_analysis: Dict = None) -> Dict[str, Any]:
        """Generate comprehensive AI-powered flight analysis report with multi-aircraft support"""
        try:
            # Use comprehensive analysis if provided (new multi-aircraft system)
            if comprehensive_analysis:
                return await self._generate_comprehensive_report(log_data, comprehensive_analysis)
            
            # Legacy mode - use provided parameters
            if risk_score is None or anomalies is None:
                raise ValueError("Either comprehensive_analysis or risk_score+anomalies must be provided")
            
            # Prepare summary statistics
            flight_stats = self._get_flight_statistics(log_data)
            
            # Generate AI summary
            ai_summary = await self._generate_ai_summary(flight_stats, risk_score, anomalies, shap_values or {})
            
            # Create comprehensive report
            report = {
                'report_id': f"DBX_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now().isoformat(),
                'flight_statistics': flight_stats,
                'risk_assessment': {
                    'overall_score': float(risk_score),
                    'level': self._get_risk_level(risk_score),
                    'description': self._get_risk_description(risk_score)
                },
                'anomalies': anomalies,
                'feature_analysis': shap_values or {},
                'ai_summary': ai_summary,
                'recommendations': self._generate_recommendations(risk_score, anomalies),
                'technical_details': self._get_technical_details(log_data)
            }
            
            return report
            
        except Exception as e:
            logging.error(f"Error generating report: {e}")
            return self._generate_fallback_report(log_data, risk_score or 0.5, anomalies or [])
    
    async def _generate_comprehensive_report(self, log_data: pd.DataFrame, analysis: Dict) -> Dict[str, Any]:
        """Generate report using comprehensive multi-aircraft analysis"""
        try:
            # Extract data from comprehensive analysis
            aircraft_type = analysis.get('aircraft_type', 'unknown')
            aircraft_confidence = analysis.get('aircraft_confidence', 0.0)
            risk_score = analysis.get('risk_score', 0.0)
            risk_level = analysis.get('risk_level', 'UNKNOWN')
            anomalies = analysis.get('anomalies', [])
            flight_phases = analysis.get('flight_phases', {})
            performance_metrics = analysis.get('performance_metrics', {})
            
            # Prepare enhanced flight statistics
            flight_stats = self._get_enhanced_flight_statistics(log_data, aircraft_type, performance_metrics)
            
            # Generate aircraft-specific AI summary
            ai_summary = await self._generate_aircraft_specific_summary(
                flight_stats, risk_score, anomalies, aircraft_type, flight_phases, performance_metrics
            )
            
            # Create comprehensive multi-aircraft report
            report = {
                'report_id': f"DBX_MA_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now().isoformat(),
                'aircraft_detection': {
                    'type': aircraft_type,
                    'confidence': aircraft_confidence,
                    'detection_method': 'multi_aircraft_analyzer'
                },
                'flight_statistics': flight_stats,
                'flight_phases': flight_phases,
                'performance_metrics': performance_metrics,
                'risk_assessment': {
                    'overall_score': float(risk_score),
                    'level': risk_level,
                    'description': self._get_aircraft_risk_description(risk_score, aircraft_type)
                },
                'anomalies': anomalies,
                'ai_summary': ai_summary,
                'recommendations': self._generate_aircraft_recommendations(risk_score, anomalies, aircraft_type),
                'technical_details': self._get_enhanced_technical_details(log_data, analysis),
                'system_version': 'multi_aircraft_v2.0'
            }
            
            return report
            
        except Exception as e:
            logging.error(f"Error generating comprehensive report: {e}")
            return self._generate_fallback_report(log_data, analysis.get('risk_score', 0.5), analysis.get('anomalies', []))
    
    def _get_flight_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract key flight statistics"""
        stats = {}
        
        try:
            if 'timestamp' in df.columns:
                duration = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
                stats['flight_duration'] = f"{duration:.0f} seconds"
            
            if 'altitude' in df.columns:
                stats['max_altitude'] = f"{df['altitude'].max():.1f} m"
                stats['avg_altitude'] = f"{df['altitude'].mean():.1f} m"
            
            if 'battery_voltage' in df.columns:
                stats['min_battery'] = f"{df['battery_voltage'].min():.2f} V"
                stats['battery_consumption'] = f"{df['battery_voltage'].iloc[0] - df['battery_voltage'].iloc[-1]:.2f} V"
            
            if 'speed' in df.columns:
                stats['max_speed'] = f"{df['speed'].max():.1f} m/s"
                stats['avg_speed'] = f"{df['speed'].mean():.1f} m/s"
            
            stats['total_data_points'] = len(df)
            
        except Exception as e:
            logging.warning(f"Error calculating flight statistics: {e}")
        
        return stats
    
    async def _generate_ai_summary(self, 
                                 flight_stats: Dict, 
                                 risk_score: float, 
                                 anomalies: List[Dict], 
                                 shap_values: Dict) -> str:
        """Generate AI-powered flight summary using Gemini"""
        try:
            if not settings.GEMINI_API_KEY:
                return self._generate_template_summary(flight_stats, risk_score, anomalies)
            
            # Prepare context for LLM
            context = {
                'flight_stats': flight_stats,
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score),
                'anomaly_count': len(anomalies),
                'top_anomalies': anomalies[:3] if anomalies else [],
                'key_features': shap_values.get('top_features', [])[:3]
            }
            
            prompt = self._build_analysis_prompt(context)
            
            # Add system instruction to the prompt
            full_prompt = "You are an expert drone flight analyst. Provide clear, actionable insights about flight safety.\n\n" + prompt
            
            # Call Gemini API
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.3,
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            logging.error(f"Error generating AI summary: {e}")
            return self._generate_template_summary(flight_stats, risk_score, anomalies)
    
    def _build_analysis_prompt(self, context: Dict) -> str:
        """Build prompt for LLM analysis"""
        prompt = f"""
        Analyze this drone flight data and provide a professional summary:

        Flight Statistics:
        - Duration: {context['flight_stats'].get('flight_duration', 'Unknown')}
        - Max Altitude: {context['flight_stats'].get('max_altitude', 'Unknown')}
        - Battery Usage: {context['flight_stats'].get('battery_consumption', 'Unknown')}
        - Max Speed: {context['flight_stats'].get('max_speed', 'Unknown')}

        Risk Assessment:
        - Risk Score: {context['risk_score']:.2f} ({context['risk_level']})
        - Anomalies Detected: {context['anomaly_count']}

        Key Issues Found:
        """
        
        for anomaly in context['top_anomalies']:
            prompt += f"- {anomaly.get('description', 'Unknown issue')}\n"
        
        prompt += f"""
        Top Contributing Factors:
        """
        
        for feature in context['key_features']:
            prompt += f"- {feature.get('feature', 'Unknown').replace('_', ' ').title()}: {feature.get('importance', 0):.3f} impact\n"
        
        prompt += """
        
        Please provide:
        1. A clear summary of the flight performance
        2. Key safety concerns (if any)
        3. Specific recommendations for the pilot
        4. Overall flight assessment
        
        Keep the response concise, professional, and actionable.
        """
        
        return prompt
    
    def _generate_template_summary(self, flight_stats: Dict, risk_score: float, anomalies: List[Dict]) -> str:
        """Generate template-based summary when LLM is not available"""
        risk_level = self._get_risk_level(risk_score)
        
        summary = f"Flight Analysis Summary - Risk Level: {risk_level}\n\n"
        
        # Flight performance
        duration = flight_stats.get('flight_duration', 'Unknown')
        max_alt = flight_stats.get('max_altitude', 'Unknown')
        summary += f"Flight Duration: {duration}\n"
        summary += f"Maximum Altitude: {max_alt}\n"
        
        # Risk assessment
        if risk_score < 0.3:
            summary += "\n✅ FLIGHT ASSESSMENT: Normal flight parameters detected. No significant safety concerns."
        elif risk_score < 0.7:
            summary += "\n⚠️ FLIGHT ASSESSMENT: Some anomalies detected. Recommend reviewing flight data."
        else:
            summary += "\n❌ FLIGHT ASSESSMENT: Multiple anomalies detected. Immediate attention required."
        
        # Key issues
        if anomalies:
            summary += f"\n\nKey Issues Detected ({len(anomalies)}):\n"
            for i, anomaly in enumerate(anomalies[:3], 1):
                summary += f"{i}. {anomaly.get('description', 'Unknown anomaly')}\n"
        
        # Recommendations
        summary += "\n" + self._get_recommendations_text(risk_score, anomalies)
        
        return summary
    
    def _generate_recommendations(self, risk_score: float, anomalies: List[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Risk-based recommendations
        if risk_score > 0.7:
            recommendations.append("Immediate inspection of drone and components required")
            recommendations.append("Ground the aircraft until issues are resolved")
        elif risk_score > 0.3:
            recommendations.append("Schedule maintenance check within 48 hours")
            recommendations.append("Monitor flight parameters closely on next flights")
        
        # Anomaly-specific recommendations
        for anomaly in anomalies[:5]:
            desc = anomaly.get('description', '').lower()
            if 'battery' in desc:
                recommendations.append("Check battery health and connections")
            elif 'motor' in desc:
                recommendations.append("Inspect motor performance and balance")
            elif 'gps' in desc:
                recommendations.append("Verify GPS antenna and signal reception")
            elif 'vibration' in desc:
                recommendations.append("Check propeller balance and mounting")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Continue normal flight operations")
            recommendations.append("Regular maintenance schedule recommended")
        
        # Remove duplicates
        return list(set(recommendations))
    
    def _get_recommendations_text(self, risk_score: float, anomalies: List[Dict]) -> str:
        """Get formatted recommendations text"""
        recommendations = self._generate_recommendations(risk_score, anomalies)
        
        text = "RECOMMENDATIONS:\n"
        for i, rec in enumerate(recommendations, 1):
            text += f"{i}. {rec}\n"
        
        return text
    
    def _get_technical_details(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract technical details for the report"""
        details = {
            'data_quality': {
                'total_samples': len(df),
                'missing_values': df.isnull().sum().sum(),
                'data_completeness': f"{(1 - df.isnull().sum().sum() / df.size) * 100:.1f}%"
            },
            'sensor_summary': {},
            'analysis_metadata': {
                'model_version': settings.MODEL_VERSION,
                'analysis_timestamp': datetime.now().isoformat(),
                'processing_time': '< 2 seconds'
            }
        }
        
        # Sensor-specific summaries
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col in ['altitude', 'battery_voltage', 'speed', 'temperature']:
                details['sensor_summary'][col] = {
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'mean': float(df[col].mean()),
                    'std': float(df[col].std())
                }
        
        return details
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to level"""
        if score < 0.3:
            return "LOW"
        elif score < 0.7:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _get_risk_description(self, score: float) -> str:
        """Get risk description"""
        if score < 0.3:
            return "Flight parameters within normal range"
        elif score < 0.7:
            return "Some anomalies detected, monitoring recommended"
        else:
            return "Multiple anomalies detected, immediate attention required"
    
    def _generate_fallback_report(self, df: pd.DataFrame, risk_score: float, anomalies: List[Dict]) -> Dict[str, Any]:
        """Generate basic report when full generation fails"""
        return {
            'report_id': f"DBX_FALLBACK_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'risk_assessment': {
                'overall_score': float(risk_score),
                'level': self._get_risk_level(risk_score),
                'description': self._get_risk_description(risk_score)
            },
            'anomalies': anomalies,
            'ai_summary': f"Basic analysis completed. Risk score: {risk_score:.2f}",
            'recommendations': self._generate_recommendations(risk_score, anomalies),
            'status': 'basic_analysis_only'
        }
    
    def _get_enhanced_flight_statistics(self, df: pd.DataFrame, aircraft_type: str, 
                                       performance_metrics: Dict) -> Dict[str, Any]:
        """Extract enhanced flight statistics with aircraft-specific metrics"""
        stats = self._get_flight_statistics(df)  # Get base statistics
        
        # Add aircraft-specific statistics
        stats['aircraft_type'] = aircraft_type
        
        if aircraft_type == 'fixed_wing':
            if 'airspeed' in df.columns:
                stats['cruise_airspeed'] = f"{df['airspeed'].mean():.1f} m/s"
                stats['max_airspeed'] = f"{df['airspeed'].max():.1f} m/s"
            if 'motor_rpm' in df.columns:
                stats['avg_engine_rpm'] = f"{df['motor_rpm'].mean():.0f} RPM"
        
        elif aircraft_type == 'multirotor':
            motor_cols = [col for col in df.columns if 'motor' in col.lower() and 'rpm' in col.lower()]
            if motor_cols:
                motor_means = [df[col].mean() for col in motor_cols]
                stats['motor_balance'] = f"{np.std(motor_means):.1f} RPM deviation"
            
            vib_cols = ['vibration_x', 'vibration_y', 'vibration_z', 'vibration_w']
            if any(col in df.columns for col in vib_cols):
                total_vib = 0
                vib_count = 0
                for col in vib_cols:
                    if col in df.columns:
                        total_vib += df[col].abs().mean()
                        vib_count += 1
                if vib_count > 0:
                    stats['avg_vibration'] = f"{total_vib/vib_count:.2f}"
        
        elif aircraft_type == 'vtol':
            if 'transition_mode' in df.columns:
                transition_time = len(df[df['transition_mode'] == 1]) * 0.1
                stats['transition_time'] = f"{transition_time:.1f} seconds"
            if 'airspeed' in df.columns:
                stats['cruise_airspeed'] = f"{df['airspeed'].mean():.1f} m/s"
        
        # Add performance metrics to stats
        stats.update(performance_metrics)
        
        return stats
    
    async def _generate_aircraft_specific_summary(self, flight_stats: Dict, risk_score: float, 
                                                anomalies: List[Dict], aircraft_type: str, 
                                                flight_phases: Dict, performance_metrics: Dict) -> str:
        """Generate aircraft-specific AI summary using Gemini"""
        try:
            if not settings.GEMINI_API_KEY:
                return self._generate_aircraft_template_summary(flight_stats, risk_score, anomalies, aircraft_type)
            
            # Prepare aircraft-specific context
            context = {
                'aircraft_type': aircraft_type,
                'flight_stats': flight_stats,
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score),
                'anomaly_count': len(anomalies),
                'top_anomalies': anomalies[:3] if anomalies else [],
                'flight_phases': flight_phases,
                'performance_metrics': performance_metrics
            }
            
            prompt = self._build_aircraft_analysis_prompt(context)
            
            # Add aircraft-specific system instruction
            system_instruction = f"You are an expert {aircraft_type.replace('_', ' ')} aircraft flight analyst. Provide clear, actionable insights about flight safety specific to this aircraft type."
            full_prompt = system_instruction + "\n\n" + prompt
            
            # Call Gemini API
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=600,
                    temperature=0.3,
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            logging.error(f"Error generating aircraft-specific AI summary: {e}")
            return self._generate_aircraft_template_summary(flight_stats, risk_score, anomalies, aircraft_type)
    
    def _build_aircraft_analysis_prompt(self, context: Dict) -> str:
        """Build aircraft-specific prompt for LLM analysis"""
        aircraft_type = context['aircraft_type']
        
        prompt = f"""
        Analyze this {aircraft_type.replace('_', ' ')} flight data and provide a professional summary:

        Aircraft Type: {aircraft_type.upper()}
        Flight Statistics:
        - Duration: {context['flight_stats'].get('flight_duration', 'Unknown')}
        - Max Altitude: {context['flight_stats'].get('max_altitude', 'Unknown')}
        - Battery Usage: {context['flight_stats'].get('battery_consumption', 'Unknown')}
        """
        
        # Add aircraft-specific statistics
        if aircraft_type == 'fixed_wing':
            prompt += f"""
        - Cruise Airspeed: {context['flight_stats'].get('cruise_airspeed', 'Unknown')}
        - Engine Performance: {context['performance_metrics'].get('engine_performance', 'Unknown')}
        """
        elif aircraft_type == 'multirotor':
            prompt += f"""
        - Motor Balance: {context['flight_stats'].get('motor_balance', 'Unknown')}
        - Vibration Level: {context['flight_stats'].get('avg_vibration', 'Unknown')}
        """
        elif aircraft_type == 'vtol':
            prompt += f"""
        - Transition Time: {context['flight_stats'].get('transition_time', 'Unknown')}
        - Cruise Airspeed: {context['flight_stats'].get('cruise_airspeed', 'Unknown')}
        """
        
        prompt += f"""
        Flight Phases:
        """
        for phase, duration in context['flight_phases'].items():
            prompt += f"- {phase.replace('_', ' ').title()}: {duration}\n"
        
        prompt += f"""
        Risk Assessment:
        - Risk Score: {context['risk_score']:.2f} ({context['risk_level']})
        - Anomalies Detected: {context['anomaly_count']}

        Key Issues Found:
        """
        
        for anomaly in context['top_anomalies']:
            prompt += f"- {anomaly.get('description', 'Unknown issue')} (Severity: {anomaly.get('severity', 'Unknown')})\n"
        
        prompt += f"""
        
        Please provide a {aircraft_type.replace('_', ' ')}-specific analysis including:
        1. Aircraft type-specific flight performance assessment
        2. Critical safety concerns for this aircraft type
        3. Specific maintenance recommendations
        4. Operational recommendations for future flights
        5. Overall flight assessment with aircraft-specific context
        
        Keep the response concise, professional, and actionable for {aircraft_type.replace('_', ' ')} operations.
        """
        
        return prompt
    
    def _generate_aircraft_template_summary(self, flight_stats: Dict, risk_score: float, 
                                          anomalies: List[Dict], aircraft_type: str) -> str:
        """Generate aircraft-specific template summary when LLM is not available"""
        risk_level = self._get_risk_level(risk_score)
        
        summary = f"{aircraft_type.replace('_', ' ').title()} Flight Analysis - Risk Level: {risk_level}\n\n"
        
        # Flight performance
        duration = flight_stats.get('flight_duration', 'Unknown')
        max_alt = flight_stats.get('max_altitude', 'Unknown')
        summary += f"Flight Duration: {duration}\n"
        summary += f"Maximum Altitude: {max_alt}\n"
        
        # Aircraft-specific metrics
        if aircraft_type == 'fixed_wing':
            summary += f"Cruise Airspeed: {flight_stats.get('cruise_airspeed', 'Unknown')}\n"
        elif aircraft_type == 'multirotor':
            summary += f"Motor Balance: {flight_stats.get('motor_balance', 'Unknown')}\n"
        elif aircraft_type == 'vtol':
            summary += f"Transition Time: {flight_stats.get('transition_time', 'Unknown')}\n"
        
        # Risk assessment
        if risk_score < 0.3:
            summary += f"\n✅ {aircraft_type.upper()} ASSESSMENT: Normal flight parameters detected. No significant safety concerns."
        elif risk_score < 0.7:
            summary += f"\n⚠️ {aircraft_type.upper()} ASSESSMENT: Some anomalies detected. Recommend reviewing flight data."
        else:
            summary += f"\n❌ {aircraft_type.upper()} ASSESSMENT: Multiple anomalies detected. Immediate attention required."
        
        # Key issues
        if anomalies:
            summary += f"\n\nKey Issues Detected ({len(anomalies)}):\n"
            for i, anomaly in enumerate(anomalies[:3], 1):
                summary += f"{i}. {anomaly.get('description', 'Unknown anomaly')} ({anomaly.get('severity', 'Unknown')})\n"
        
        # Aircraft-specific recommendations
        summary += "\n" + self._get_aircraft_recommendations_text(risk_score, anomalies, aircraft_type)
        
        return summary
    
    def _generate_aircraft_recommendations(self, risk_score: float, anomalies: List[Dict], aircraft_type: str) -> List[str]:
        """Generate aircraft-specific actionable recommendations"""
        recommendations = []
        
        # Risk-based recommendations
        if risk_score > 0.7:
            recommendations.append(f"Immediate inspection of {aircraft_type.replace('_', ' ')} and components required")
            recommendations.append("Ground the aircraft until issues are resolved")
        elif risk_score > 0.3:
            recommendations.append("Schedule maintenance check within 48 hours")
            recommendations.append("Monitor flight parameters closely on next flights")
        
        # Aircraft-specific anomaly recommendations
        for anomaly in anomalies[:5]:
            desc = anomaly.get('description', '').lower()
            
            if aircraft_type == 'fixed_wing':
                if 'airspeed' in desc or 'stall' in desc:
                    recommendations.append("Check airspeed sensor calibration and pitot tube")
                elif 'engine' in desc or 'motor' in desc:
                    recommendations.append("Inspect engine/motor and fuel/battery system")
                elif 'elevator' in desc or 'aileron' in desc:
                    recommendations.append("Check control surface linkages and servo operation")
            
            elif aircraft_type == 'multirotor':
                if 'motor' in desc and 'asymmetry' in desc:
                    recommendations.append("Balance and calibrate all motor ESCs")
                elif 'vibration' in desc:
                    recommendations.append("Check propeller balance and motor mounting")
                elif 'attitude' in desc or 'tilt' in desc:
                    recommendations.append("Calibrate IMU and check frame rigidity")
            
            elif aircraft_type == 'vtol':
                if 'transition' in desc:
                    recommendations.append("Review transition flight envelope and control logic")
                elif 'lift motor' in desc:
                    recommendations.append("Inspect vertical lift motor system")
                elif 'forward motor' in desc:
                    recommendations.append("Check forward propulsion system")
            
            # Common recommendations
            if 'battery' in desc:
                recommendations.append("Check battery health and connections")
            elif 'gps' in desc:
                recommendations.append("Verify GPS antenna and signal reception")
        
        # General aircraft-specific recommendations
        if not recommendations:
            if aircraft_type == 'fixed_wing':
                recommendations.append("Continue normal fixed-wing operations")
                recommendations.append("Regular engine and control surface inspection recommended")
            elif aircraft_type == 'multirotor':
                recommendations.append("Continue normal multirotor operations")
                recommendations.append("Regular motor and propeller inspection recommended")
            elif aircraft_type == 'vtol':
                recommendations.append("Continue normal VTOL operations")
                recommendations.append("Regular transition system inspection recommended")
        
        # Remove duplicates
        return list(set(recommendations))
    
    def _get_aircraft_recommendations_text(self, risk_score: float, anomalies: List[Dict], aircraft_type: str) -> str:
        """Get formatted aircraft-specific recommendations text"""
        recommendations = self._generate_aircraft_recommendations(risk_score, anomalies, aircraft_type)
        
        text = f"{aircraft_type.upper()} RECOMMENDATIONS:\n"
        for i, rec in enumerate(recommendations, 1):
            text += f"{i}. {rec}\n"
        
        return text
    
    def _get_aircraft_risk_description(self, score: float, aircraft_type: str) -> str:
        """Get aircraft-specific risk description"""
        aircraft_name = aircraft_type.replace('_', ' ')
        
        if score < 0.3:
            return f"{aircraft_name.title()} flight parameters within normal range"
        elif score < 0.7:
            return f"Some {aircraft_name} anomalies detected, monitoring recommended"
        else:
            return f"Multiple {aircraft_name} anomalies detected, immediate attention required"
    
    def _get_enhanced_technical_details(self, df: pd.DataFrame, analysis: Dict) -> Dict[str, Any]:
        """Extract enhanced technical details with multi-aircraft analysis"""
        details = self._get_technical_details(df)  # Get base technical details
        
        # Add multi-aircraft specific details
        details['multi_aircraft_analysis'] = {
            'aircraft_type': analysis.get('aircraft_type', 'unknown'),
            'detection_confidence': analysis.get('aircraft_confidence', 0.0),
            'specialized_features_used': True,
            'analysis_method': 'multi_aircraft_detector_v2.0'
        }
        
        # Add aircraft-specific sensor summaries
        aircraft_type = analysis.get('aircraft_type', 'unknown')
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        if aircraft_type == 'fixed_wing':
            for col in numeric_columns:
                if col in ['airspeed', 'motor_rpm', 'throttle_position', 'elevator_position', 'aileron_position']:
                    if col not in details['sensor_summary']:
                        details['sensor_summary'][col] = {
                            'min': float(df[col].min()),
                            'max': float(df[col].max()),
                            'mean': float(df[col].mean()),
                            'std': float(df[col].std())
                        }
        
        elif aircraft_type == 'multirotor':
            motor_cols = [col for col in numeric_columns if 'motor' in col.lower() and 'rpm' in col.lower()]
            for col in motor_cols:
                if col not in details['sensor_summary']:
                    details['sensor_summary'][col] = {
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'mean': float(df[col].mean()),
                        'std': float(df[col].std())
                    }
        
        return details
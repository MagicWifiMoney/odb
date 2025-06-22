"""
Win Probability Service
High-level service for managing win probability predictions and model training
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import json
import os

from .win_probability_engine import (
    WinProbabilityMLEngine, WinProbabilityModel, WinPrediction, ModelPerformance
)
from .cache_service import get_cache, CacheStrategy
from .perplexity_client import get_perplexity_client
from ..config.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class WinProbabilityService:
    """Main service for win probability predictions"""
    
    def __init__(self):
        self.ml_engine = WinProbabilityMLEngine(WinProbabilityModel.ENSEMBLE)
        self.cache = get_cache()
        self.supabase = get_supabase_client()
        self.model_path = "/tmp/win_probability_model.joblib"
        
    async def predict_win_probability(self, opportunity_id: str, company_id: str = None) -> WinPrediction:
        """Predict win probability for a specific opportunity"""
        logger.info(f"Predicting win probability for opportunity {opportunity_id}")
        
        try:
            # Get opportunity data
            opportunity = await self._fetch_opportunity(opportunity_id)
            if not opportunity:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            
            # Use provided company_id or default to current user's company
            if not company_id:
                company_id = "default_company"  # This would come from auth context
            
            # Get company history
            company_history = await self._fetch_company_history(company_id)
            
            # Get market data
            market_data = await self._get_market_data()
            
            # Get historical outcomes
            historical_outcomes = await self._fetch_historical_outcomes()
            
            # Ensure model is trained
            await self._ensure_model_trained()
            
            # Make prediction
            prediction = self.ml_engine.predict_win_probability(
                opportunity, company_history, market_data, historical_outcomes
            )
            
            # Store prediction in database
            await self._store_prediction(prediction)
            
            # Get AI insights about the prediction
            ai_insights = await self._get_ai_prediction_insights(prediction, opportunity)
            
            # Add AI insights to prediction
            prediction_dict = prediction.__dict__.copy()
            prediction_dict['ai_insights'] = ai_insights
            prediction_dict['prediction_date'] = prediction.prediction_date.isoformat()
            
            return prediction_dict
            
        except Exception as e:
            logger.error(f"Win probability prediction failed: {e}")
            return {"error": str(e)}
    
    async def batch_predict_opportunities(self, opportunity_ids: List[str], 
                                        company_id: str = None) -> List[Dict[str, Any]]:
        """Predict win probabilities for multiple opportunities"""
        logger.info(f"Batch predicting {len(opportunity_ids)} opportunities")
        
        predictions = []
        for opp_id in opportunity_ids:
            try:
                prediction = await self.predict_win_probability(opp_id, company_id)
                predictions.append(prediction)
            except Exception as e:
                logger.warning(f"Failed to predict {opp_id}: {e}")
                predictions.append({
                    "opportunity_id": opp_id,
                    "error": str(e)
                })
        
        return predictions
    
    async def get_top_opportunities(self, company_id: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get opportunities ranked by win probability"""
        logger.info(f"Getting top {limit} opportunities by win probability")
        
        try:
            # Get recent opportunities
            opportunities = await self._fetch_recent_opportunities(limit * 2)  # Get more to filter
            
            # Predict win probabilities
            predictions = []
            for opp in opportunities:
                try:
                    prediction = await self.predict_win_probability(opp['id'], company_id)
                    if 'error' not in prediction:
                        prediction['opportunity'] = opp
                        predictions.append(prediction)
                except Exception as e:
                    logger.warning(f"Prediction failed for {opp.get('id')}: {e}")
                    continue
            
            # Sort by win probability
            predictions.sort(key=lambda x: x.get('win_probability', 0), reverse=True)
            
            return predictions[:limit]
            
        except Exception as e:
            logger.error(f"Get top opportunities failed: {e}")
            return {"error": str(e)}
    
    async def train_model(self, retrain: bool = False) -> Dict[str, Any]:
        """Train the win probability model"""
        logger.info("Training win probability model")
        
        try:
            # Check if model exists and is recent
            if not retrain and os.path.exists(self.model_path):
                model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(self.model_path))
                if model_age < timedelta(days=7):
                    logger.info("Using existing recent model")
                    self.ml_engine.load_model(self.model_path)
                    return {"status": "Model loaded from cache", "age_days": model_age.days}
            
            # Fetch training data
            training_data = await self._prepare_training_data()
            
            if not training_data:
                return {"error": "Insufficient training data"}
            
            # Prepare features and labels
            X, y = self.ml_engine.prepare_training_data(
                training_data['opportunities'],
                training_data['company_histories'],
                training_data['market_data'],
                training_data['historical_outcomes']
            )
            
            if len(X) < 100:
                logger.warning(f"Limited training data: {len(X)} samples")
                return {"error": f"Insufficient training data: {len(X)} samples (minimum 100 required)"}
            
            # Train models
            performance = self.ml_engine.train_models(X, y)
            
            # Save model
            self.ml_engine.save_model(self.model_path)
            
            # Store training results
            await self._store_training_results(performance)
            
            logger.info("Model training completed successfully")
            
            return {
                "status": "Training completed",
                "training_samples": len(X),
                "features": len(X.columns),
                "performance": {
                    model_name: {
                        "accuracy": perf.accuracy,
                        "auc_roc": perf.auc_roc,
                        "precision": perf.precision,
                        "recall": perf.recall
                    }
                    for model_name, perf in performance.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {"error": str(e)}
    
    async def get_model_performance(self) -> Dict[str, Any]:
        """Get current model performance metrics"""
        try:
            # Get latest training results from database
            response = self.supabase.table('win_predictions').select(
                'model_version, accuracy, precision, recall, auc_roc, training_date'
            ).order('training_date', desc=True).limit(1).execute()
            
            if response.data:
                latest = response.data[0]
                return {
                    "model_version": latest.get('model_version'),
                    "training_date": latest.get('training_date'),
                    "performance": {
                        "accuracy": latest.get('accuracy'),
                        "precision": latest.get('precision'),
                        "recall": latest.get('recall'),
                        "auc_roc": latest.get('auc_roc')
                    },
                    "model_status": "trained" if self.ml_engine.is_trained else "not_trained"
                }
            else:
                return {"error": "No training history found"}
                
        except Exception as e:
            logger.error(f"Get model performance failed: {e}")
            return {"error": str(e)}
    
    async def analyze_prediction_factors(self, opportunity_id: str) -> Dict[str, Any]:
        """Analyze what factors most influence the prediction"""
        try:
            prediction = await self.predict_win_probability(opportunity_id)
            
            if 'error' in prediction:
                return prediction
            
            # Get feature importance
            feature_importance = prediction.get('feature_importance', {})
            
            # Sort by importance
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            # Categorize features
            feature_categories = {
                'company_experience': [],
                'opportunity_characteristics': [],
                'competitive_landscape': [],
                'historical_patterns': []
            }
            
            for feature, importance in sorted_features[:15]:  # Top 15 features
                if 'company' in feature:
                    feature_categories['company_experience'].append({
                        'feature': feature,
                        'importance': importance,
                        'description': self._get_feature_description(feature)
                    })
                elif any(x in feature for x in ['estimated_value', 'days_to_respond', 'keyword']):
                    feature_categories['opportunity_characteristics'].append({
                        'feature': feature,
                        'importance': importance,
                        'description': self._get_feature_description(feature)
                    })
                elif any(x in feature for x in ['competition', 'agency_avg', 'seasonal']):
                    feature_categories['competitive_landscape'].append({
                        'feature': feature,
                        'importance': importance,
                        'description': self._get_feature_description(feature)
                    })
                else:
                    feature_categories['historical_patterns'].append({
                        'feature': feature,
                        'importance': importance,
                        'description': self._get_feature_description(feature)
                    })
            
            return {
                "opportunity_id": opportunity_id,
                "win_probability": prediction.get('win_probability'),
                "feature_analysis": feature_categories,
                "key_factors": {
                    "top_positive": sorted_features[:5],
                    "top_negative": sorted_features[-5:] if len(sorted_features) > 10 else []
                }
            }
            
        except Exception as e:
            logger.error(f"Factor analysis failed: {e}")
            return {"error": str(e)}
    
    async def _fetch_opportunity(self, opportunity_id: str) -> Optional[Dict]:
        """Fetch opportunity data from database"""
        try:
            response = self.supabase.table('opportunities').select('*').eq('id', opportunity_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to fetch opportunity {opportunity_id}: {e}")
            return None
    
    async def _fetch_company_history(self, company_id: str) -> List[Dict]:
        """Fetch company bidding history"""
        try:
            # In a real implementation, this would fetch from a company_bids table
            # For now, return simulated data
            return [
                {
                    "opportunity_id": f"hist_{i}",
                    "agency_name": ["DOD", "VA", "HHS"][i % 3],
                    "contract_value": 100000 + (i * 50000),
                    "won": i % 4 == 0,  # 25% win rate
                    "date": (datetime.now() - timedelta(days=i * 30)).isoformat(),
                    "keywords": ["security", "software", "consulting"]
                }
                for i in range(20)
            ]
        except Exception as e:
            logger.error(f"Failed to fetch company history: {e}")
            return []
    
    async def _get_market_data(self) -> Dict[str, Any]:
        """Get market competition and trend data"""
        try:
            # Cache market data for 24 hours
            cache_key = "market_data_v1"
            cached = await self.cache.get(cache_key, CacheStrategy.LONG_TERM)
            
            if cached:
                return cached
            
            # Simulate market data - in real implementation, this would be calculated from historical data
            market_data = {
                "agencies": {
                    "DOD": {"avg_competitors": 8.5, "win_rate_variance": 0.3, "contracts_per_month": 45},
                    "VA": {"avg_competitors": 6.2, "win_rate_variance": 0.25, "contracts_per_month": 25},
                    "HHS": {"avg_competitors": 5.8, "win_rate_variance": 0.2, "contracts_per_month": 30},
                    "DHS": {"avg_competitors": 7.1, "win_rate_variance": 0.28, "contracts_per_month": 20}
                },
                "value_buckets": {
                    "micro": {"avg_competitors": 3.2, "small_business_rate": 0.8},
                    "small": {"avg_competitors": 4.5, "small_business_rate": 0.6},
                    "medium": {"avg_competitors": 6.8, "small_business_rate": 0.4},
                    "large": {"avg_competitors": 9.2, "small_business_rate": 0.2},
                    "mega": {"avg_competitors": 12.5, "small_business_rate": 0.1}
                },
                "keywords": {
                    "cloud": {"competition_score": 0.8},
                    "security": {"competition_score": 0.9},
                    "software": {"competition_score": 0.7},
                    "consulting": {"competition_score": 0.6},
                    "research": {"competition_score": 0.5}
                },
                "seasonal_patterns": {
                    "1": 1.2, "2": 1.1, "3": 1.3, "4": 1.0, "5": 0.9, "6": 0.8,
                    "7": 0.7, "8": 0.8, "9": 1.1, "10": 1.2, "11": 1.1, "12": 0.9
                }
            }
            
            await self.cache.set(cache_key, market_data, CacheStrategy.LONG_TERM)
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return {}
    
    async def _fetch_historical_outcomes(self) -> List[Dict]:
        """Fetch historical opportunity outcomes for similarity matching"""
        try:
            # Simulate historical outcomes - in real implementation, fetch from database
            historical = []
            for i in range(500):
                historical.append({
                    "id": f"hist_opp_{i}",
                    "agency_name": ["DOD", "VA", "HHS", "DHS"][i % 4],
                    "contract_value": 50000 + (i * 10000),
                    "won": i % 5 == 0,  # 20% overall win rate
                    "timeline_days": 30 + (i % 60),
                    "competitor_count": 3 + (i % 8),
                    "keywords": ["security", "software", "cloud"][:(i % 3) + 1],
                    "date": (datetime.now() - timedelta(days=i * 7)).isoformat()
                })
            
            return historical
            
        except Exception as e:
            logger.error(f"Failed to fetch historical outcomes: {e}")
            return []
    
    async def _fetch_recent_opportunities(self, limit: int = 50) -> List[Dict]:
        """Fetch recent opportunities for ranking"""
        try:
            response = self.supabase.table('opportunities').select('*').order(
                'posted_date', desc=True
            ).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Failed to fetch recent opportunities: {e}")
            return []
    
    async def _prepare_training_data(self) -> Dict[str, Any]:
        """Prepare comprehensive training data"""
        try:
            # Get historical opportunities with outcomes
            # In real implementation, this would join opportunities with bid_outcomes table
            training_opportunities = []
            
            # Simulate training data
            for i in range(1000):
                won = i % 5 == 0  # 20% win rate
                training_opportunities.append({
                    "id": f"train_opp_{i}",
                    "company_id": f"company_{i % 50}",  # 50 companies
                    "title": f"Training Opportunity {i}",
                    "agency_name": ["DOD", "VA", "HHS", "DHS"][i % 4],
                    "estimated_value": 50000 + (i * 25000),
                    "posted_date": (datetime.now() - timedelta(days=i * 3)).isoformat(),
                    "due_date": (datetime.now() - timedelta(days=i * 3 - 30)).isoformat(),
                    "keywords": json.dumps(["security", "software", "cloud"][:(i % 3) + 1]),
                    "won": won
                })
            
            # Get company histories
            company_histories = {}
            for company_id in set(opp["company_id"] for opp in training_opportunities):
                company_histories[company_id] = await self._fetch_company_history(company_id)
            
            # Get market data and historical outcomes
            market_data = await self._get_market_data()
            historical_outcomes = await self._fetch_historical_outcomes()
            
            return {
                "opportunities": training_opportunities,
                "company_histories": company_histories,
                "market_data": market_data,
                "historical_outcomes": historical_outcomes
            }
            
        except Exception as e:
            logger.error(f"Failed to prepare training data: {e}")
            return None
    
    async def _ensure_model_trained(self):
        """Ensure model is trained and ready for predictions"""
        if not self.ml_engine.is_trained:
            if os.path.exists(self.model_path):
                logger.info("Loading existing model")
                self.ml_engine.load_model(self.model_path)
            else:
                logger.info("No trained model found, training new model")
                result = await self.train_model()
                if "error" in result:
                    raise ValueError(f"Model training failed: {result['error']}")
    
    async def _store_prediction(self, prediction: WinPrediction):
        """Store prediction in database"""
        try:
            prediction_data = {
                "opportunity_id": prediction.opportunity_id,
                "win_probability": prediction.win_probability,
                "confidence_score": prediction.confidence_score,
                "risk_factors": prediction.risk_factors,
                "success_factors": prediction.success_factors,
                "competitive_analysis": prediction.competitive_analysis,
                "model_version": prediction.model_version,
                "prediction_date": prediction.prediction_date.isoformat(),
                "feature_importance": prediction.feature_importance
            }
            
            self.supabase.table('win_predictions').upsert(prediction_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store prediction: {e}")
    
    async def _store_training_results(self, performance: Dict[str, ModelPerformance]):
        """Store model training results"""
        try:
            for model_name, perf in performance.items():
                training_data = {
                    "model_name": model_name,
                    "model_version": self.ml_engine.model_version,
                    "accuracy": perf.accuracy,
                    "precision": perf.precision,
                    "recall": perf.recall,
                    "auc_roc": perf.auc_roc,
                    "feature_importance": perf.feature_importance,
                    "cross_val_scores": perf.cross_val_scores,
                    "confusion_matrix": perf.confusion_matrix,
                    "training_date": datetime.now().isoformat()
                }
                
                self.supabase.table('model_training_results').insert(training_data).execute()
                
        except Exception as e:
            logger.error(f"Failed to store training results: {e}")
    
    async def _get_ai_prediction_insights(self, prediction: WinPrediction, opportunity: Dict) -> Dict[str, Any]:
        """Get AI-powered insights about the prediction"""
        try:
            client = get_perplexity_client()
            
            context = {
                "opportunity": {
                    "title": opportunity.get('title'),
                    "agency": opportunity.get('agency_name'),
                    "value": opportunity.get('estimated_value'),
                    "timeline": opportunity.get('days_to_respond', 30)
                },
                "prediction": {
                    "win_probability": prediction.win_probability,
                    "confidence": prediction.confidence_score,
                    "risk_factors": prediction.risk_factors[:3],
                    "success_factors": prediction.success_factors[:3]
                }
            }
            
            query = f"""
            Analyze this government contract opportunity prediction and provide strategic insights:
            
            Win Probability: {prediction.win_probability:.1%}
            Confidence: {prediction.confidence_score:.1%}
            
            Key Risk Factors: {', '.join(prediction.risk_factors[:3])}
            Key Success Factors: {', '.join(prediction.success_factors[:3])}
            
            Provide:
            1. Strategic recommendations for improving win probability
            2. Key areas to focus on in the proposal
            3. Potential competitive advantages to highlight
            4. Timeline and resource allocation suggestions
            """
            
            async with client:
                result = await client.get_business_insights(query, context)
                
                if result and 'choices' in result:
                    return {
                        "analysis": result['choices'][0]['message']['content'],
                        "confidence": 0.8,
                        "generated_at": datetime.now().isoformat()
                    }
            
        except Exception as e:
            logger.warning(f"AI insights generation failed: {e}")
        
        return {"analysis": "AI insights temporarily unavailable"}
    
    def _get_feature_description(self, feature_name: str) -> str:
        """Get human-readable description of feature"""
        descriptions = {
            "company_agency_win_rate": "Historical win rate with this agency",
            "company_total_wins": "Total number of contracts won",
            "company_recent_win_rate": "Win rate in last 2 years",
            "estimated_value": "Contract estimated value",
            "days_to_respond": "Days available for proposal submission",
            "industry_competition": "Level of competition in this industry",
            "similar_opp_win_rate": "Win rate on historically similar opportunities",
            "agency_avg_competitors": "Average number of competitors for this agency",
            "company_keyword_alignment": "Alignment between company expertise and opportunity requirements",
            "is_high_value": "Whether this is a high-value contract (>$1M)",
            "agency_historical_win_rate": "Overall win rate with this agency historically"
        }
        
        return descriptions.get(feature_name, feature_name.replace('_', ' ').title())

# Global service instance
_win_probability_service: Optional[WinProbabilityService] = None

def get_win_probability_service() -> WinProbabilityService:
    """Get the global win probability service instance"""
    global _win_probability_service
    if _win_probability_service is None:
        _win_probability_service = WinProbabilityService()
    return _win_probability_service
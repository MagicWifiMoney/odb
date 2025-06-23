"""
Win Probability ML Engine
Machine learning pipeline for predicting contract win probability
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import pickle
import json
from dataclasses import dataclass
from enum import Enum

# ML imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.pipeline import Pipeline
import joblib

logger = logging.getLogger(__name__)

class WinProbabilityModel(Enum):
    """Available ML models for win probability prediction"""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    LOGISTIC_REGRESSION = "logistic_regression"
    ENSEMBLE = "ensemble"

class FeatureType(Enum):
    """Types of features for win probability prediction"""
    COMPANY_FEATURES = "company"
    OPPORTUNITY_FEATURES = "opportunity"
    COMPETITIVE_FEATURES = "competitive"
    HISTORICAL_FEATURES = "historical"
    MARKET_FEATURES = "market"

@dataclass
class WinPrediction:
    """Win probability prediction result"""
    opportunity_id: str
    win_probability: float
    confidence_score: float
    risk_factors: List[str]
    success_factors: List[str]
    competitive_analysis: Dict[str, Any]
    model_version: str
    prediction_date: datetime
    feature_importance: Dict[str, float]

@dataclass
class ModelPerformance:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    feature_importance: Dict[str, float]
    cross_val_scores: List[float]
    confusion_matrix: List[List[int]]

class FeatureEngineering:
    """Feature engineering for win probability prediction"""
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.feature_selectors = {}
        
    def extract_company_features(self, opportunity: Dict, company_history: List[Dict]) -> Dict[str, float]:
        """Extract company-specific features"""
        features = {}
        
        # Company experience metrics
        features['company_total_wins'] = len([h for h in company_history if h.get('won', False)])
        features['company_total_bids'] = len(company_history)
        features['company_win_rate'] = features['company_total_wins'] / max(1, features['company_total_bids'])
        
        # Company size indicators (estimate from historical contract values)
        historical_values = [h.get('contract_value', 0) for h in company_history if h.get('contract_value')]
        features['company_avg_contract_value'] = np.mean(historical_values) if historical_values else 0
        features['company_max_contract_value'] = max(historical_values) if historical_values else 0
        
        # Recent performance (last 2 years)
        recent_cutoff = datetime.now() - timedelta(days=730)
        recent_history = [h for h in company_history 
                         if datetime.fromisoformat(h.get('date', '2020-01-01')) > recent_cutoff]
        
        features['company_recent_wins'] = len([h for h in recent_history if h.get('won', False)])
        features['company_recent_bids'] = len(recent_history)
        features['company_recent_win_rate'] = features['company_recent_wins'] / max(1, features['company_recent_bids'])
        
        # Agency experience
        agency = opportunity.get('agency_name', '')
        agency_history = [h for h in company_history if h.get('agency_name') == agency]
        features['company_agency_experience'] = len(agency_history)
        features['company_agency_wins'] = len([h for h in agency_history if h.get('won', False)])
        features['company_agency_win_rate'] = features['company_agency_wins'] / max(1, features['company_agency_experience'])
        
        # Industry/keyword alignment
        opp_keywords = set(opportunity.get('keywords', []))
        if isinstance(opp_keywords, str):
            try:
                opp_keywords = set(json.loads(opp_keywords))
            except:
                opp_keywords = set()
        
        keyword_matches = 0
        for hist in company_history:
            hist_keywords = hist.get('keywords', [])
            if isinstance(hist_keywords, str):
                try:
                    hist_keywords = json.loads(hist_keywords)
                except:
                    hist_keywords = []
            keyword_matches += len(opp_keywords.intersection(set(hist_keywords)))
        
        features['company_keyword_alignment'] = keyword_matches / max(1, len(company_history))
        
        return features
    
    def extract_opportunity_features(self, opportunity: Dict) -> Dict[str, float]:
        """Extract opportunity-specific features"""
        features = {}
        
        # Basic opportunity characteristics
        features['estimated_value'] = float(opportunity.get('estimated_value', 0))
        features['estimated_value_log'] = np.log1p(features['estimated_value'])
        
        # Timeline features
        posted_date = datetime.fromisoformat(opportunity.get('posted_date', datetime.now().isoformat()))
        due_date = datetime.fromisoformat(opportunity.get('due_date', datetime.now().isoformat()))
        
        features['days_to_respond'] = (due_date - posted_date).days
        features['days_since_posted'] = (datetime.now() - posted_date).days
        
        # Opportunity complexity indicators
        title_length = len(opportunity.get('title', ''))
        description_length = len(opportunity.get('description', ''))
        
        features['title_length'] = title_length
        features['description_length'] = description_length
        features['description_complexity'] = description_length / max(1, title_length)
        
        # Keywords analysis
        keywords = opportunity.get('keywords', [])
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except:
                keywords = []
        
        features['keyword_count'] = len(keywords)
        
        # High-value opportunity indicators
        features['is_high_value'] = 1.0 if features['estimated_value'] > 1000000 else 0.0
        features['is_urgent'] = 1.0 if features['days_to_respond'] < 14 else 0.0
        features['is_recent'] = 1.0 if features['days_since_posted'] < 7 else 0.0
        
        # Source type encoding
        source_type = opportunity.get('source_type', 'unknown')
        features['source_federal'] = 1.0 if 'federal' in source_type.lower() else 0.0
        features['source_state'] = 1.0 if 'state' in source_type.lower() else 0.0
        features['source_local'] = 1.0 if 'local' in source_type.lower() else 0.0
        
        return features
    
    def extract_competitive_features(self, opportunity: Dict, market_data: Dict) -> Dict[str, float]:
        """Extract competitive landscape features"""
        features = {}
        
        # Market competition indicators
        agency_name = opportunity.get('agency_name', '')
        estimated_value = float(opportunity.get('estimated_value', 0))
        
        # Historical competition for this agency
        agency_data = market_data.get('agencies', {}).get(agency_name, {})
        features['agency_avg_competitors'] = agency_data.get('avg_competitors', 5.0)
        features['agency_win_rate_variance'] = agency_data.get('win_rate_variance', 0.2)
        features['agency_contract_frequency'] = agency_data.get('contracts_per_month', 1.0)
        
        # Value-based competition
        value_bucket = self._get_value_bucket(estimated_value)
        value_data = market_data.get('value_buckets', {}).get(value_bucket, {})
        features['value_bucket_competition'] = value_data.get('avg_competitors', 5.0)
        features['value_bucket_small_biz_rate'] = value_data.get('small_business_rate', 0.3)
        
        # Industry competition
        keywords = opportunity.get('keywords', [])
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except:
                keywords = []
        
        industry_competition = 0.0
        for keyword in keywords[:3]:  # Top 3 keywords
            keyword_data = market_data.get('keywords', {}).get(keyword, {})
            industry_competition += keyword_data.get('competition_score', 0.5)
        
        features['industry_competition'] = industry_competition / max(1, len(keywords[:3]))
        
        # Timing-based competition
        month = datetime.fromisoformat(opportunity.get('posted_date', datetime.now().isoformat())).month
        features['seasonal_competition'] = market_data.get('seasonal_patterns', {}).get(str(month), 1.0)
        
        return features
    
    def extract_historical_features(self, opportunity: Dict, historical_outcomes: List[Dict]) -> Dict[str, float]:
        """Extract features based on historical similar opportunities"""
        features = {}
        
        # Find similar opportunities
        similar_opportunities = self._find_similar_opportunities(opportunity, historical_outcomes)
        
        if similar_opportunities:
            # Historical win rates for similar opportunities
            wins = [o for o in similar_opportunities if o.get('won', False)]
            features['similar_opp_win_rate'] = len(wins) / len(similar_opportunities)
            
            # Average characteristics of won opportunities
            if wins:
                features['winning_avg_value'] = np.mean([o.get('contract_value', 0) for o in wins])
                features['winning_avg_timeline'] = np.mean([o.get('timeline_days', 30) for o in wins])
            else:
                features['winning_avg_value'] = 0
                features['winning_avg_timeline'] = 30
            
            # Competition analysis
            features['similar_avg_competitors'] = np.mean([o.get('competitor_count', 5) for o in similar_opportunities])
            
        else:
            # Default values when no similar opportunities found
            features['similar_opp_win_rate'] = 0.2  # Conservative default
            features['winning_avg_value'] = 0
            features['winning_avg_timeline'] = 30
            features['similar_avg_competitors'] = 5
        
        # Historical agency performance
        agency_name = opportunity.get('agency_name', '')
        agency_opportunities = [o for o in historical_outcomes if o.get('agency_name') == agency_name]
        
        if agency_opportunities:
            agency_wins = [o for o in agency_opportunities if o.get('won', False)]
            features['agency_historical_win_rate'] = len(agency_wins) / len(agency_opportunities)
            features['agency_avg_timeline'] = np.mean([o.get('timeline_days', 30) for o in agency_opportunities])
        else:
            features['agency_historical_win_rate'] = 0.2
            features['agency_avg_timeline'] = 30
        
        return features
    
    def _get_value_bucket(self, value: float) -> str:
        """Categorize contract value into buckets"""
        if value < 25000:
            return "micro"
        elif value < 150000:
            return "small"
        elif value < 750000:
            return "medium"
        elif value < 5000000:
            return "large"
        else:
            return "mega"
    
    def _find_similar_opportunities(self, opportunity: Dict, historical_outcomes: List[Dict]) -> List[Dict]:
        """Find historically similar opportunities for comparison"""
        target_keywords = set(opportunity.get('keywords', []))
        if isinstance(target_keywords, str):
            try:
                target_keywords = set(json.loads(target_keywords))
            except:
                target_keywords = set()
        
        target_value = float(opportunity.get('estimated_value', 0))
        target_agency = opportunity.get('agency_name', '')
        
        similar = []
        for hist_opp in historical_outcomes:
            similarity_score = 0
            
            # Keyword similarity
            hist_keywords = set(hist_opp.get('keywords', []))
            if isinstance(hist_keywords, str):
                try:
                    hist_keywords = set(json.loads(hist_keywords))
                except:
                    hist_keywords = set()
            
            keyword_overlap = len(target_keywords.intersection(hist_keywords))
            if keyword_overlap > 0:
                similarity_score += keyword_overlap * 0.4
            
            # Value similarity (within 50% range)
            hist_value = float(hist_opp.get('contract_value', 0))
            if target_value > 0 and hist_value > 0:
                value_ratio = min(target_value, hist_value) / max(target_value, hist_value)
                if value_ratio > 0.5:
                    similarity_score += value_ratio * 0.3
            
            # Agency match
            if hist_opp.get('agency_name') == target_agency:
                similarity_score += 0.3
            
            # Include if similarity score is high enough
            if similarity_score > 0.5:
                similar.append(hist_opp)
        
        # Return top 20 most similar
        return sorted(similar, key=lambda x: self._calculate_similarity_score(opportunity, x), reverse=True)[:20]
    
    def _calculate_similarity_score(self, opp1: Dict, opp2: Dict) -> float:
        """Calculate detailed similarity score between two opportunities"""
        score = 0.0
        
        # Keyword similarity
        kw1 = set(opp1.get('keywords', []))
        kw2 = set(opp2.get('keywords', []))
        if isinstance(kw1, str):
            try:
                kw1 = set(json.loads(kw1))
            except:
                kw1 = set()
        if isinstance(kw2, str):
            try:
                kw2 = set(json.loads(kw2))
            except:
                kw2 = set()
        
        if kw1 and kw2:
            jaccard = len(kw1.intersection(kw2)) / len(kw1.union(kw2))
            score += jaccard * 0.4
        
        # Value similarity
        val1 = float(opp1.get('estimated_value', 0))
        val2 = float(opp2.get('contract_value', opp2.get('estimated_value', 0)))
        if val1 > 0 and val2 > 0:
            ratio = min(val1, val2) / max(val1, val2)
            score += ratio * 0.3
        
        # Agency match
        if opp1.get('agency_name') == opp2.get('agency_name'):
            score += 0.3
        
        return score

class WinProbabilityMLEngine:
    """Main ML engine for win probability prediction"""
    
    def __init__(self, model_type: WinProbabilityModel = WinProbabilityModel.ENSEMBLE):
        self.model_type = model_type
        self.models = {}
        self.feature_engineering = FeatureEngineering()
        self.feature_columns = []
        self.is_trained = False
        self.model_version = "1.0.0"
        
    def prepare_training_data(self, training_opportunities: List[Dict], 
                            company_histories: Dict[str, List[Dict]],
                            market_data: Dict[str, Any],
                            historical_outcomes: List[Dict]) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data with feature engineering"""
        logger.info(f"Preparing training data for {len(training_opportunities)} opportunities")
        
        features_list = []
        labels = []
        
        for opp in training_opportunities:
            try:
                # Extract all feature types
                company_id = opp.get('company_id', 'unknown')
                company_history = company_histories.get(company_id, [])
                
                company_features = self.feature_engineering.extract_company_features(opp, company_history)
                opp_features = self.feature_engineering.extract_opportunity_features(opp)
                competitive_features = self.feature_engineering.extract_competitive_features(opp, market_data)
                historical_features = self.feature_engineering.extract_historical_features(opp, historical_outcomes)
                
                # Combine all features
                all_features = {
                    **company_features,
                    **opp_features,
                    **competitive_features,
                    **historical_features
                }
                
                features_list.append(all_features)
                labels.append(1 if opp.get('won', False) else 0)
                
            except Exception as e:
                logger.warning(f"Error processing opportunity {opp.get('id', 'unknown')}: {e}")
                continue
        
        # Convert to DataFrame
        X = pd.DataFrame(features_list)
        y = pd.Series(labels)
        
        # Store feature columns for future use
        self.feature_columns = X.columns.tolist()
        
        logger.info(f"Prepared training data: {len(X)} samples, {len(X.columns)} features")
        return X, y
    
    def train_models(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, ModelPerformance]:
        """Train ML models for win probability prediction"""
        logger.info("Training win probability models")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Define models
        model_configs = {
            WinProbabilityModel.RANDOM_FOREST: RandomForestClassifier(
                n_estimators=100, 
                max_depth=10, 
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            ),
            WinProbabilityModel.GRADIENT_BOOSTING: GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            WinProbabilityModel.LOGISTIC_REGRESSION: LogisticRegression(
                random_state=42,
                max_iter=1000
            )
        }
        
        performance_results = {}
        
        for model_type, model in model_configs.items():
            logger.info(f"Training {model_type.value} model")
            
            # Create pipeline with preprocessing
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('feature_selection', SelectKBest(f_classif, k=min(50, len(X.columns)))),
                ('classifier', model)
            ])
            
            # Train model
            pipeline.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = pipeline.predict(X_test)
            y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
            
            # Calculate metrics
            performance = self._calculate_performance_metrics(y_test, y_pred, y_pred_proba, pipeline, X)
            performance_results[model_type.value] = performance
            
            # Store trained model
            self.models[model_type.value] = pipeline
            
            logger.info(f"{model_type.value} - AUC: {performance.auc_roc:.3f}, Accuracy: {performance.accuracy:.3f}")
        
        # Create ensemble model
        if len(self.models) > 1:
            logger.info("Creating ensemble model")
            ensemble_performance = self._create_ensemble_model(X_test, y_test)
            performance_results['ensemble'] = ensemble_performance
        
        self.is_trained = True
        return performance_results
    
    def predict_win_probability(self, opportunity: Dict, 
                              company_history: List[Dict],
                              market_data: Dict[str, Any],
                              historical_outcomes: List[Dict]) -> WinPrediction:
        """Predict win probability for a single opportunity"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Extract features
        company_features = self.feature_engineering.extract_company_features(opportunity, company_history)
        opp_features = self.feature_engineering.extract_opportunity_features(opportunity)
        competitive_features = self.feature_engineering.extract_competitive_features(opportunity, market_data)
        historical_features = self.feature_engineering.extract_historical_features(opportunity, historical_outcomes)
        
        # Combine features
        all_features = {
            **company_features,
            **opp_features,
            **competitive_features,
            **historical_features
        }
        
        # Ensure all features are present
        feature_vector = []
        for feature_name in self.feature_columns:
            feature_vector.append(all_features.get(feature_name, 0.0))
        
        X = pd.DataFrame([feature_vector], columns=self.feature_columns)
        
        # Get predictions from all models
        predictions = {}
        feature_importances = {}
        
        for model_name, model in self.models.items():
            if model_name != 'ensemble':
                prob = model.predict_proba(X)[0][1]
                predictions[model_name] = prob
                
                # Get feature importance
                if hasattr(model.named_steps['classifier'], 'feature_importances_'):
                    selected_features = model.named_steps['feature_selection'].get_support()
                    importances = model.named_steps['classifier'].feature_importances_
                    selected_feature_names = [self.feature_columns[i] for i, selected in enumerate(selected_features) if selected]
                    feature_importances[model_name] = dict(zip(selected_feature_names, importances))
        
        # Ensemble prediction (weighted average)
        if self.model_type == WinProbabilityModel.ENSEMBLE and len(predictions) > 1:
            weights = {'random_forest': 0.4, 'gradient_boosting': 0.4, 'logistic_regression': 0.2}
            win_probability = sum(predictions[model] * weights.get(model, 1.0/len(predictions)) 
                                for model in predictions) / sum(weights.values())
        else:
            model_name = self.model_type.value
            win_probability = predictions.get(model_name, predictions[list(predictions.keys())[0]])
        
        # Calculate confidence score based on model agreement
        confidence_score = 1.0 - np.std(list(predictions.values())) if len(predictions) > 1 else 0.8
        
        # Analyze risk and success factors
        risk_factors, success_factors = self._analyze_factors(all_features, win_probability)
        
        # Competitive analysis
        competitive_analysis = {
            "estimated_competitors": all_features.get('agency_avg_competitors', 5),
            "competition_level": "High" if all_features.get('industry_competition', 0.5) > 0.7 else "Medium" if all_features.get('industry_competition', 0.5) > 0.4 else "Low",
            "market_position": "Strong" if all_features.get('company_agency_win_rate', 0) > 0.3 else "Average" if all_features.get('company_agency_win_rate', 0) > 0.1 else "Weak"
        }
        
        return WinPrediction(
            opportunity_id=opportunity.get('id', 'unknown'),
            win_probability=float(win_probability),
            confidence_score=float(confidence_score),
            risk_factors=risk_factors,
            success_factors=success_factors,
            competitive_analysis=competitive_analysis,
            model_version=self.model_version,
            prediction_date=datetime.now(),
            feature_importance=feature_importances.get(self.model_type.value, {})
        )
    
    def _calculate_performance_metrics(self, y_true, y_pred, y_pred_proba, model, X) -> ModelPerformance:
        """Calculate comprehensive model performance metrics"""
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)
        auc_roc = roc_auc_score(y_true, y_pred_proba)
        
        # Cross-validation scores
        cv_scores = cross_val_score(model, X, y_true, cv=5, scoring='roc_auc')
        
        # Feature importance
        feature_importance = {}
        if hasattr(model.named_steps['classifier'], 'feature_importances_'):
            selected_features = model.named_steps['feature_selection'].get_support()
            importances = model.named_steps['classifier'].feature_importances_
            selected_feature_names = [self.feature_columns[i] for i, selected in enumerate(selected_features) if selected]
            feature_importance = dict(zip(selected_feature_names, importances))
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred).tolist()
        
        return ModelPerformance(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            auc_roc=auc_roc,
            feature_importance=feature_importance,
            cross_val_scores=cv_scores.tolist(),
            confusion_matrix=cm
        )
    
    def _create_ensemble_model(self, X_test, y_test) -> ModelPerformance:
        """Create and evaluate ensemble model"""
        ensemble_predictions = []
        
        for model in self.models.values():
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X_test)[:, 1]
                ensemble_predictions.append(proba)
        
        if ensemble_predictions:
            # Average predictions
            ensemble_proba = np.mean(ensemble_predictions, axis=0)
            ensemble_pred = (ensemble_proba > 0.5).astype(int)
            
            return self._calculate_performance_metrics(y_test, ensemble_pred, ensemble_proba, None, None)
        
        return None
    
    def _analyze_factors(self, features: Dict[str, float], win_probability: float) -> Tuple[List[str], List[str]]:
        """Analyze risk and success factors based on features"""
        risk_factors = []
        success_factors = []
        
        # Company experience factors
        if features.get('company_agency_win_rate', 0) > 0.3:
            success_factors.append("Strong track record with this agency")
        elif features.get('company_agency_win_rate', 0) < 0.1:
            risk_factors.append("Limited experience with this agency")
        
        # Competition factors
        if features.get('industry_competition', 0.5) > 0.7:
            risk_factors.append("High industry competition")
        elif features.get('industry_competition', 0.5) < 0.3:
            success_factors.append("Low competitive pressure")
        
        # Value factors
        if features.get('is_high_value', 0) == 1.0:
            if features.get('company_max_contract_value', 0) > features.get('estimated_value', 0):
                success_factors.append("Experience with similar-value contracts")
            else:
                risk_factors.append("Contract value exceeds historical experience")
        
        # Timeline factors
        if features.get('is_urgent', 0) == 1.0:
            risk_factors.append("Short response timeline")
        elif features.get('days_to_respond', 30) > 30:
            success_factors.append("Adequate time for proposal preparation")
        
        # Historical performance
        if features.get('similar_opp_win_rate', 0.2) > 0.4:
            success_factors.append("Strong win rate on similar opportunities")
        elif features.get('similar_opp_win_rate', 0.2) < 0.15:
            risk_factors.append("Poor historical performance on similar opportunities")
        
        # Keyword alignment
        if features.get('company_keyword_alignment', 0) > 1.0:
            success_factors.append("Strong keyword/expertise alignment")
        elif features.get('company_keyword_alignment', 0) < 0.5:
            risk_factors.append("Limited expertise alignment")
        
        return risk_factors, success_factors
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'models': self.models,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type.value,
            'model_version': self.model_version,
            'feature_engineering': self.feature_engineering
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        model_data = joblib.load(filepath)
        
        self.models = model_data['models']
        self.feature_columns = model_data['feature_columns']
        self.model_type = WinProbabilityModel(model_data['model_type'])
        self.model_version = model_data['model_version']
        self.feature_engineering = model_data['feature_engineering']
        self.is_trained = True
        
        logger.info(f"Model loaded from {filepath}")
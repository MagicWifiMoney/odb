"""
Advanced Trend & Anomaly Analysis Engine
AI-powered trend detection and anomaly identification for government opportunities
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import logging
from collections import defaultdict
import json

# Scientific computing
from scipy import stats
from scipy.signal import find_peaks
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA

# Time series analysis
try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning("statsmodels not available, some advanced features disabled")

from .cache_service import get_cache, CacheStrategy
from .perplexity_client import get_perplexity_client, QueryType

# Setup logging
logger = logging.getLogger(__name__)

class TrendType(Enum):
    """Types of trends that can be detected"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"
    VOLATILE = "volatile"
    STABLE = "stable"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"

class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    VOLUME_SPIKE = "volume_spike"
    VALUE_OUTLIER = "value_outlier"
    TIMING_ANOMALY = "timing_anomaly"
    PATTERN_BREAK = "pattern_break"
    SEASONAL_DEVIATION = "seasonal_deviation"
    KEYWORD_SURGE = "keyword_surge"
    AGENCY_ANOMALY = "agency_anomaly"

@dataclass
class TrendAnalysisConfig:
    """Configuration for trend analysis"""
    window_sizes: List[int] = None  # [7, 30, 90, 365]
    anomaly_threshold: float = 2.5  # Standard deviations
    min_data_points: int = 30
    seasonal_periods: List[int] = None  # [7, 30, 365]
    confidence_level: float = 0.95
    
    def __post_init__(self):
        if self.window_sizes is None:
            self.window_sizes = [7, 30, 90, 365]
        if self.seasonal_periods is None:
            self.seasonal_periods = [7, 30, 365]

@dataclass
class TrendResult:
    """Result of trend analysis"""
    metric_name: str
    trend_type: TrendType
    strength: float  # 0-1 scale
    confidence: float  # 0-1 scale
    slope: float
    r_squared: float
    start_date: datetime
    end_date: datetime
    data_points: int
    seasonal_component: Optional[float] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['trend_type'] = self.trend_type.value
        result['start_date'] = self.start_date.isoformat()
        result['end_date'] = self.end_date.isoformat()
        return result

@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    timestamp: datetime
    metric_name: str
    anomaly_type: AnomalyType
    severity: float  # 0-10 scale
    expected_value: float
    actual_value: float
    confidence: float
    context: Dict[str, Any]
    description: str
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['anomaly_type'] = self.anomaly_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

class TimeSeriesAnalyzer:
    """Core time series analysis engine"""
    
    def __init__(self, config: TrendAnalysisConfig = None):
        self.config = config or TrendAnalysisConfig()
        self.cache = get_cache()
        self.scaler = StandardScaler()
    
    def preprocess_data(self, data: pd.DataFrame, datetime_col: str, value_col: str) -> pd.DataFrame:
        """Preprocess time series data"""
        logger.info(f"Preprocessing {len(data)} data points")
        
        # Ensure datetime column is datetime type
        data[datetime_col] = pd.to_datetime(data[datetime_col])
        
        # Sort by datetime
        data = data.sort_values(datetime_col).reset_index(drop=True)
        
        # Handle missing values
        data[value_col] = data[value_col].fillna(method='ffill').fillna(method='bfill')
        
        # Remove outliers using IQR method
        Q1 = data[value_col].quantile(0.25)
        Q3 = data[value_col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Log outliers but don't remove them (they might be anomalies we want to detect)
        outliers = data[(data[value_col] < lower_bound) | (data[value_col] > upper_bound)]
        if len(outliers) > 0:
            logger.info(f"Found {len(outliers)} potential outliers")
        
        return data
    
    def detect_trend(self, data: pd.DataFrame, datetime_col: str, value_col: str) -> TrendResult:
        """Detect trend in time series data"""
        if len(data) < self.config.min_data_points:
            raise ValueError(f"Insufficient data points: {len(data)} < {self.config.min_data_points}")
        
        # Create time index
        data = data.copy()
        data['time_index'] = range(len(data))
        
        # Linear regression for trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(data['time_index'], data[value_col])
        
        # Determine trend type
        r_squared = r_value ** 2
        trend_strength = abs(r_value)
        
        if r_squared > 0.7 and abs(slope) > 0.01:
            if slope > 0:
                trend_type = TrendType.INCREASING
            else:
                trend_type = TrendType.DECREASING
        elif r_squared > 0.3:
            trend_type = TrendType.LINEAR
        else:
            # Check for other patterns
            trend_type = self._classify_complex_trend(data[value_col])
        
        # Calculate confidence
        confidence = max(0, min(1, (r_squared + (1 - p_value)) / 2))
        
        return TrendResult(
            metric_name=value_col,
            trend_type=trend_type,
            strength=trend_strength,
            confidence=confidence,
            slope=slope,
            r_squared=r_squared,
            start_date=data[datetime_col].min(),
            end_date=data[datetime_col].max(),
            data_points=len(data)
        )
    
    def _classify_complex_trend(self, series: pd.Series) -> TrendType:
        """Classify complex trend patterns"""
        # Calculate volatility
        volatility = series.std() / series.mean() if series.mean() != 0 else 0
        
        if volatility > 0.5:
            return TrendType.VOLATILE
        elif volatility < 0.1:
            return TrendType.STABLE
        
        # Check for exponential growth
        try:
            log_series = np.log(series + 1e-10)  # Add small constant to avoid log(0)
            slope, _, r_value, _, _ = stats.linregress(range(len(log_series)), log_series)
            if r_value ** 2 > 0.7 and slope > 0.01:
                return TrendType.EXPONENTIAL
        except:
            pass
        
        return TrendType.STABLE
    
    def detect_anomalies(self, data: pd.DataFrame, datetime_col: str, value_col: str) -> List[AnomalyResult]:
        """Detect anomalies in time series data"""
        anomalies = []
        
        # Statistical anomaly detection
        anomalies.extend(self._detect_statistical_anomalies(data, datetime_col, value_col))
        
        # Machine learning anomaly detection
        anomalies.extend(self._detect_ml_anomalies(data, datetime_col, value_col))
        
        # Pattern-based anomaly detection
        anomalies.extend(self._detect_pattern_anomalies(data, datetime_col, value_col))
        
        # Sort by severity
        anomalies.sort(key=lambda x: x.severity, reverse=True)
        
        return anomalies
    
    def _detect_statistical_anomalies(self, data: pd.DataFrame, datetime_col: str, value_col: str) -> List[AnomalyResult]:
        """Detect statistical anomalies using Z-score and IQR methods"""
        anomalies = []
        
        # Z-score method
        z_scores = np.abs(stats.zscore(data[value_col]))
        z_threshold = self.config.anomaly_threshold
        
        for idx, z_score in enumerate(z_scores):
            if z_score > z_threshold:
                severity = min(10, z_score / z_threshold * 5)
                expected_value = data[value_col].mean()
                actual_value = data[value_col].iloc[idx]
                
                anomalies.append(AnomalyResult(
                    timestamp=data[datetime_col].iloc[idx],
                    metric_name=value_col,
                    anomaly_type=AnomalyType.VALUE_OUTLIER,
                    severity=severity,
                    expected_value=expected_value,
                    actual_value=actual_value,
                    confidence=min(1.0, z_score / 5),
                    context={"z_score": z_score, "method": "statistical"},
                    description=f"Value {actual_value:.2f} deviates {z_score:.2f} standard deviations from mean {expected_value:.2f}"
                ))
        
        return anomalies
    
    def _detect_ml_anomalies(self, data: pd.DataFrame, datetime_col: str, value_col: str) -> List[AnomalyResult]:
        """Detect anomalies using machine learning methods"""
        anomalies = []
        
        if len(data) < 50:  # Need sufficient data for ML
            return anomalies
        
        try:
            # Prepare features
            features = self._create_features(data, value_col)
            
            # Isolation Forest
            iso_forest = IsolationForest(contamination=0.05, random_state=42)
            anomaly_scores = iso_forest.fit_predict(features)
            anomaly_probabilities = iso_forest.score_samples(features)
            
            for idx, (score, prob) in enumerate(zip(anomaly_scores, anomaly_probabilities)):
                if score == -1:  # Anomaly detected
                    severity = min(10, abs(prob) * 10)
                    
                    anomalies.append(AnomalyResult(
                        timestamp=data[datetime_col].iloc[idx],
                        metric_name=value_col,
                        anomaly_type=AnomalyType.PATTERN_BREAK,
                        severity=severity,
                        expected_value=data[value_col].median(),
                        actual_value=data[value_col].iloc[idx],
                        confidence=min(1.0, abs(prob)),
                        context={"isolation_score": prob, "method": "isolation_forest"},
                        description=f"ML algorithm detected unusual pattern with confidence {abs(prob):.3f}"
                    ))
        
        except Exception as e:
            logger.warning(f"ML anomaly detection failed: {e}")
        
        return anomalies
    
    def _detect_pattern_anomalies(self, data: pd.DataFrame, datetime_col: str, value_col: str) -> List[AnomalyResult]:
        """Detect pattern-based anomalies"""
        anomalies = []
        
        # Volume spikes (sudden increases)
        rolling_mean = data[value_col].rolling(window=7, min_periods=1).mean()
        rolling_std = data[value_col].rolling(window=7, min_periods=1).std()
        
        for idx in range(len(data)):
            if idx < 7:  # Skip first few points
                continue
            
            current_value = data[value_col].iloc[idx]
            expected_value = rolling_mean.iloc[idx-1]
            std_value = rolling_std.iloc[idx-1]
            
            if std_value > 0 and current_value > expected_value + 3 * std_value:
                severity = min(10, (current_value - expected_value) / std_value)
                
                anomalies.append(AnomalyResult(
                    timestamp=data[datetime_col].iloc[idx],
                    metric_name=value_col,
                    anomaly_type=AnomalyType.VOLUME_SPIKE,
                    severity=severity,
                    expected_value=expected_value,
                    actual_value=current_value,
                    confidence=0.8,
                    context={"rolling_window": 7, "method": "volume_spike"},
                    description=f"Volume spike: {current_value:.2f} vs expected {expected_value:.2f}"
                ))
        
        return anomalies
    
    def _create_features(self, data: pd.DataFrame, value_col: str) -> np.ndarray:
        """Create features for ML anomaly detection"""
        features = []
        
        # Rolling statistics
        for window in [3, 7, 14]:
            features.append(data[value_col].rolling(window=window, min_periods=1).mean())
            features.append(data[value_col].rolling(window=window, min_periods=1).std())
        
        # Lag features
        for lag in [1, 2, 3]:
            features.append(data[value_col].shift(lag))
        
        # Time-based features
        data_copy = data.copy()
        data_copy['hour'] = pd.to_datetime(data.iloc[:, 0]).dt.hour
        data_copy['day_of_week'] = pd.to_datetime(data.iloc[:, 0]).dt.dayofweek
        features.append(data_copy['hour'])
        features.append(data_copy['day_of_week'])
        
        # Combine features
        feature_matrix = np.column_stack([f.fillna(f.mean()) for f in features])
        
        return feature_matrix

class TrendAggregator:
    """Aggregates data for trend analysis"""
    
    def __init__(self):
        self.cache = get_cache()
    
    async def aggregate_opportunities(self, opportunities: List[Dict], 
                                    analysis_type: str = "daily") -> pd.DataFrame:
        """Aggregate opportunity data for trend analysis"""
        logger.info(f"Aggregating {len(opportunities)} opportunities for {analysis_type} analysis")
        
        df = pd.DataFrame(opportunities)
        
        if df.empty:
            return df
        
        # Ensure required columns exist
        required_cols = ['posted_date', 'estimated_value', 'agency_name', 'keywords']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing columns: {missing_cols}")
            return pd.DataFrame()
        
        # Convert posted_date to datetime
        df['posted_date'] = pd.to_datetime(df['posted_date'])
        df['estimated_value'] = pd.to_numeric(df['estimated_value'], errors='coerce').fillna(0)
        
        # Create aggregation key based on analysis type
        if analysis_type == "daily":
            df['agg_key'] = df['posted_date'].dt.date
        elif analysis_type == "weekly":
            df['agg_key'] = df['posted_date'].dt.to_period('W')
        elif analysis_type == "monthly":
            df['agg_key'] = df['posted_date'].dt.to_period('M')
        else:
            df['agg_key'] = df['posted_date'].dt.date
        
        # Perform aggregations
        agg_data = []
        
        for date_key, group in df.groupby('agg_key'):
            # Basic metrics
            opportunity_count = len(group)
            total_value = group['estimated_value'].sum()
            avg_value = group['estimated_value'].mean()
            
            # Industry breakdown
            industry_breakdown = self._analyze_industries(group)
            
            # Agency breakdown
            agency_breakdown = group['agency_name'].value_counts().head(10).to_dict()
            
            # Keyword analysis
            trending_keywords = self._extract_trending_keywords(group)
            
            agg_data.append({
                'analysis_date': pd.to_datetime(str(date_key)),
                'analysis_type': analysis_type,
                'opportunity_count': opportunity_count,
                'total_value': total_value,
                'avg_value': avg_value,
                'industry_breakdown': industry_breakdown,
                'agency_breakdown': agency_breakdown,
                'trending_keywords': trending_keywords,
                'data_quality_score': self._calculate_data_quality(group)
            })
        
        result_df = pd.DataFrame(agg_data)
        result_df = result_df.sort_values('analysis_date')
        
        logger.info(f"Created {len(result_df)} aggregated data points")
        return result_df
    
    def _analyze_industries(self, group: pd.DataFrame) -> Dict[str, int]:
        """Analyze industry distribution"""
        # Simple industry classification based on keywords
        industry_keywords = {
            'defense': ['defense', 'military', 'security', 'army', 'navy', 'air force'],
            'healthcare': ['health', 'medical', 'hospital', 'care', 'drug'],
            'it': ['software', 'technology', 'computer', 'data', 'cloud', 'cyber'],
            'construction': ['construction', 'building', 'infrastructure', 'road'],
            'energy': ['energy', 'power', 'solar', 'wind', 'electric']
        }
        
        industry_counts = defaultdict(int)
        
        for _, row in group.iterrows():
            keywords = str(row.get('keywords', '')).lower()
            title = str(row.get('title', '')).lower()
            description = str(row.get('description', '')).lower()
            
            text = f"{keywords} {title} {description}"
            
            for industry, industry_keys in industry_keywords.items():
                if any(key in text for key in industry_keys):
                    industry_counts[industry] += 1
                    break
            else:
                industry_counts['other'] += 1
        
        return dict(industry_counts)
    
    def _extract_trending_keywords(self, group: pd.DataFrame) -> List[str]:
        """Extract trending keywords from opportunity data"""
        keyword_counts = defaultdict(int)
        
        for _, row in group.iterrows():
            keywords = row.get('keywords', [])
            if isinstance(keywords, str):
                try:
                    keywords = json.loads(keywords)
                except:
                    keywords = []
            
            if isinstance(keywords, list):
                for keyword in keywords:
                    if isinstance(keyword, str) and len(keyword) > 2:
                        keyword_counts[keyword.lower()] += 1
        
        # Return top 10 keywords
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, count in sorted_keywords[:10]]
    
    def _calculate_data_quality(self, group: pd.DataFrame) -> float:
        """Calculate data quality score for the group"""
        total_fields = 0
        complete_fields = 0
        
        important_fields = ['title', 'description', 'agency_name', 'estimated_value', 'due_date']
        
        for field in important_fields:
            if field in group.columns:
                total_fields += len(group)
                complete_fields += group[field].notna().sum()
        
        return complete_fields / total_fields if total_fields > 0 else 0.0

# Export key components
__all__ = [
    'TimeSeriesAnalyzer',
    'TrendAggregator', 
    'TrendAnalysisConfig',
    'TrendResult',
    'AnomalyResult',
    'TrendType',
    'AnomalyType'
]
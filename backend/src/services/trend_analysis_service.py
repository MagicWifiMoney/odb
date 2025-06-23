import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
import json
import logging

from src.database import db
from src.models.opportunity import Opportunity

logger = logging.getLogger(__name__)

class TrendAnalysisService:
    """
    Comprehensive time-series analysis service for RFP trend detection and anomaly analysis.
    Implements pandas-based data structures for efficient time-based operations.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.isolation_forest = None
        self.lof_detector = None
        
    def get_opportunities_dataframe(self, start_date: Optional[datetime] = None, 
                                  end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Load opportunities data into a pandas DataFrame with proper datetime indexing.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            DataFrame with datetime index and processed columns
        """
        try:
            # Build query
            query = db.session.query(Opportunity)
            
            if start_date:
                query = query.filter(Opportunity.posted_date >= start_date)
            if end_date:
                query = query.filter(Opportunity.posted_date <= end_date)
                
            # Execute and convert to DataFrame
            opportunities = query.all()
            
            if not opportunities:
                logger.warning("No opportunities found for the specified date range")
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for opp in opportunities:
                opp_dict = opp.to_dict()
                data.append(opp_dict)
            
            df = pd.DataFrame(data)
            
            # Convert date columns to datetime
            date_columns = ['posted_date', 'due_date', 'created_at', 'updated_at']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Set posted_date as index for time-series operations
            if 'posted_date' in df.columns:
                df = df.set_index('posted_date').sort_index()
            
            # Handle missing values
            df = self._preprocess_dataframe(df)
            
            logger.info(f"Loaded {len(df)} opportunities into DataFrame")
            return df
            
        except Exception as e:
            logger.error(f"Error loading opportunities DataFrame: {e}")
            return pd.DataFrame()
    
    def _preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the DataFrame for time-series analysis.
        
        Args:
            df: Raw opportunities DataFrame
            
        Returns:
            Preprocessed DataFrame
        """
        # Handle missing estimated_value
        df['estimated_value'] = df['estimated_value'].fillna(df['estimated_value'].median())
        
        # Extract and clean categorical data
        df['agency_name'] = df['agency_name'].fillna('Unknown')
        df['source_type'] = df['source_type'].fillna('Unknown')
        df['location'] = df['location'].fillna('Unknown')
        
        # Process keywords (handle JSON/list format)
        def process_keywords(keywords):
            if pd.isna(keywords):
                return []
            if isinstance(keywords, str):
                try:
                    return json.loads(keywords) if keywords.startswith('[') else [keywords]
                except json.JSONDecodeError:
                    return [keywords]
            return keywords if isinstance(keywords, list) else []
        
        df['keywords_processed'] = df['keywords'].apply(process_keywords)
        
        # Create derived features for analysis
        df['days_to_due'] = (df['due_date'] - df.index).dt.days
        
        # Extract time features from datetime index
        try:
            if pd.api.types.is_datetime64_any_dtype(df.index):
                df['posting_hour'] = df.index.hour
                df['posting_day_of_week'] = df.index.dayofweek  
                df['posting_month'] = df.index.month
            else:
                # Fallback for non-datetime index
                df['posting_hour'] = 0
                df['posting_day_of_week'] = 0
                df['posting_month'] = 1
        except Exception:
            # Fallback if datetime extraction fails
            df['posting_hour'] = 0
            df['posting_day_of_week'] = 0
            df['posting_month'] = 1
        
        # Create value categories
        df['value_category'] = pd.cut(df['estimated_value'], 
                                    bins=[0, 100000, 500000, 1000000, float('inf')],
                                    labels=['Small', 'Medium', 'Large', 'Enterprise'])
        
        return df
    
    def calculate_time_series_aggregations(self, df: pd.DataFrame, 
                                         analysis_type: str = 'daily') -> pd.DataFrame:
        """
        Calculate various time-series aggregations for trend analysis.
        
        Args:
            df: Preprocessed opportunities DataFrame
            analysis_type: 'daily', 'weekly', 'monthly'
            
        Returns:
            DataFrame with aggregated metrics
        """
        try:
            # Define aggregation frequency
            freq_map = {
                'daily': 'D',
                'weekly': 'W', 
                'monthly': 'M'
            }
            freq = freq_map.get(analysis_type, 'D')
            
            # Core aggregations
            agg_data = []
            
            # Group by time period
            grouped = df.groupby(pd.Grouper(freq=freq))
            
            for date, group in grouped:
                if group.empty:
                    continue
                    
                # Basic metrics
                metrics = {
                    'analysis_date': date.date(),
                    'analysis_type': analysis_type,
                    'opportunity_count': len(group),
                    'total_value': group['estimated_value'].sum(),
                    'avg_value': group['estimated_value'].mean(),
                }
                
                # Industry breakdown (using agency as proxy)
                industry_breakdown = group['agency_name'].value_counts().to_dict()
                metrics['industry_breakdown'] = industry_breakdown
                
                # Region breakdown (using location)
                region_breakdown = group['location'].value_counts().to_dict()
                metrics['region_breakdown'] = region_breakdown
                
                # Source breakdown
                agency_breakdown = group['source_type'].value_counts().to_dict()
                metrics['agency_breakdown'] = agency_breakdown
                
                # Keywords analysis
                all_keywords = []
                for keywords in group['keywords_processed']:
                    all_keywords.extend(keywords)
                
                keyword_counts = pd.Series(all_keywords).value_counts()
                metrics['trending_keywords'] = keyword_counts.head(10).to_dict()
                
                agg_data.append(metrics)
            
            if not agg_data:
                return pd.DataFrame()
                
            agg_df = pd.DataFrame(agg_data)
            agg_df['analysis_date'] = pd.to_datetime(agg_df['analysis_date'])
            agg_df = agg_df.set_index('analysis_date').sort_index()
            
            # Calculate rolling averages
            agg_df = self._calculate_rolling_metrics(agg_df)
            
            # Calculate year-over-year changes
            agg_df = self._calculate_yoy_changes(agg_df)
            
            logger.info(f"Calculated {len(agg_df)} {analysis_type} aggregations")
            return agg_df
            
        except Exception as e:
            logger.error(f"Error calculating aggregations: {e}")
            return pd.DataFrame()
    
    def _calculate_rolling_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate rolling window metrics for trend analysis.
        
        Args:
            df: Aggregated DataFrame
            
        Returns:
            DataFrame with rolling metrics added
        """
        # 7-day rolling average
        df['rolling_7_day_avg'] = df['opportunity_count'].rolling(window=7, min_periods=1).mean()
        
        # 30-day rolling average
        df['rolling_30_day_avg'] = df['opportunity_count'].rolling(window=30, min_periods=1).mean()
        
        # Rolling total value averages
        df['rolling_7_day_value'] = df['total_value'].rolling(window=7, min_periods=1).mean()
        df['rolling_30_day_value'] = df['total_value'].rolling(window=30, min_periods=1).mean()
        
        return df
    
    def _calculate_yoy_changes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate year-over-year percentage changes.
        
        Args:
            df: DataFrame with time index
            
        Returns:
            DataFrame with YoY changes added
        """
        # Calculate YoY change for opportunity count
        df['yoy_opportunity_change'] = df['opportunity_count'].pct_change(periods=365) * 100
        
        # Calculate YoY change for total value
        df['yoy_value_change'] = df['total_value'].pct_change(periods=365) * 100
        
        return df
    
    def detect_anomalies(self, df: pd.DataFrame, 
                        methods: List[str] = ['isolation_forest', 'lof', 'statistical']) -> pd.DataFrame:
        """
        Detect anomalies using multiple algorithms.
        
        Args:
            df: Time-series DataFrame
            methods: List of detection methods to use
            
        Returns:
            DataFrame with anomaly detection results
        """
        try:
            df_copy = df.copy()
            
            # Prepare features for ML algorithms
            feature_columns = ['opportunity_count', 'total_value', 'avg_value']
            if 'rolling_7_day_avg' in df.columns:
                feature_columns.extend(['rolling_7_day_avg', 'rolling_30_day_avg'])
            
            # Filter for available columns
            available_features = [col for col in feature_columns if col in df.columns]
            
            if not available_features:
                logger.warning("No suitable features found for anomaly detection")
                return df_copy
            
            # Prepare feature matrix
            feature_matrix = df_copy[available_features].fillna(0)
            
            # Scale features for ML algorithms
            if len(feature_matrix) > 1:
                scaled_features = self.scaler.fit_transform(feature_matrix)
            else:
                scaled_features = feature_matrix.values
            
            # Initialize anomaly columns
            df_copy['is_anomaly'] = False
            df_copy['anomaly_score'] = 0.0
            df_copy['anomaly_type'] = None
            
            detected_methods = []
            
            # Method 1: Isolation Forest
            if 'isolation_forest' in methods and len(feature_matrix) > 5:
                anomalies_if = self._detect_isolation_forest(scaled_features)
                df_copy['anomaly_isolation_forest'] = anomalies_if
                detected_methods.append('isolation_forest')
            
            # Method 2: Local Outlier Factor
            if 'lof' in methods and len(feature_matrix) > 10:
                anomalies_lof = self._detect_local_outlier_factor(scaled_features)
                df_copy['anomaly_lof'] = anomalies_lof
                detected_methods.append('lof')
            
            # Method 3: Statistical Methods (Z-score and MAD)
            if 'statistical' in methods:
                anomalies_stat = self._detect_statistical_anomalies(feature_matrix)
                df_copy['anomaly_statistical'] = anomalies_stat
                detected_methods.append('statistical')
            
            # Combine results
            if detected_methods:
                df_copy = self._combine_anomaly_results(df_copy, detected_methods)
            
            logger.info(f"Anomaly detection completed using methods: {detected_methods}")
            return df_copy
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return df
    
    def _detect_isolation_forest(self, features: np.ndarray, contamination: float = 0.1) -> np.ndarray:
        """
        Detect anomalies using Isolation Forest.
        
        Args:
            features: Scaled feature matrix
            contamination: Expected proportion of anomalies
            
        Returns:
            Boolean array indicating anomalies
        """
        try:
            self.isolation_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            
            predictions = self.isolation_forest.fit_predict(features)
            return predictions == -1  # Anomalies are labeled as -1
            
        except Exception as e:
            logger.error(f"Error in Isolation Forest detection: {e}")
            return np.zeros(len(features), dtype=bool)
    
    def _detect_local_outlier_factor(self, features: np.ndarray, n_neighbors: int = 20) -> np.ndarray:
        """
        Detect anomalies using Local Outlier Factor.
        
        Args:
            features: Scaled feature matrix
            n_neighbors: Number of neighbors for LOF
            
        Returns:
            Boolean array indicating anomalies
        """
        try:
            n_neighbors = min(n_neighbors, len(features) - 1)
            if n_neighbors < 1:
                return np.zeros(len(features), dtype=bool)
                
            self.lof_detector = LocalOutlierFactor(
                n_neighbors=n_neighbors,
                contamination=0.1
            )
            
            predictions = self.lof_detector.fit_predict(features)
            return predictions == -1  # Anomalies are labeled as -1
            
        except Exception as e:
            logger.error(f"Error in LOF detection: {e}")
            return np.zeros(len(features), dtype=bool)
    
    def _detect_statistical_anomalies(self, features: pd.DataFrame, threshold: float = 3.0) -> np.ndarray:
        """
        Detect anomalies using statistical methods (Z-score and MAD).
        
        Args:
            features: Feature DataFrame
            threshold: Z-score threshold for anomaly detection
            
        Returns:
            Boolean array indicating anomalies
        """
        try:
            anomalies = np.zeros(len(features), dtype=bool)
            
            for column in features.columns:
                series = features[column]
                
                # Z-score method
                z_scores = np.abs((series - series.mean()) / series.std())
                z_anomalies = z_scores > threshold
                
                # MAD method
                median = series.median()
                mad = np.median(np.abs(series - median))
                if mad > 0:
                    mad_scores = np.abs(series - median) / mad
                    mad_anomalies = mad_scores > threshold
                else:
                    mad_anomalies = np.zeros(len(series), dtype=bool)
                
                # Combine Z-score and MAD results (either method flags as anomaly)
                column_anomalies = z_anomalies | mad_anomalies
                anomalies = anomalies | column_anomalies
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error in statistical anomaly detection: {e}")
            return np.zeros(len(features), dtype=bool)
    
    def _combine_anomaly_results(self, df: pd.DataFrame, methods: List[str]) -> pd.DataFrame:
        """
        Combine results from multiple anomaly detection methods.
        
        Args:
            df: DataFrame with individual method results
            methods: List of methods used
            
        Returns:
            DataFrame with combined anomaly results
        """
        # Count how many methods flagged each point as anomalous
        method_columns = [f'anomaly_{method}' for method in methods]
        available_columns = [col for col in method_columns if col in df.columns]
        
        if not available_columns:
            return df
        
        # Calculate anomaly score based on agreement between methods
        anomaly_votes = df[available_columns].sum(axis=1)
        total_methods = len(available_columns)
        
        df['anomaly_score'] = (anomaly_votes / total_methods) * 10  # Scale to 0-10
        
        # Mark as anomaly if majority of methods agree
        df['is_anomaly'] = anomaly_votes >= (total_methods / 2)
        
        # Determine anomaly type based on which features are outliers
        df['anomaly_type'] = df.apply(self._classify_anomaly_type, axis=1)
        
        return df
    
    def _classify_anomaly_type(self, row: pd.Series) -> Optional[str]:
        """
        Classify the type of anomaly based on which metrics are unusual.
        
        Args:
            row: DataFrame row with anomaly information
            
        Returns:
            String describing the anomaly type
        """
        if not row.get('is_anomaly', False):
            return None
        
        # Analyze which metrics are unusual
        if row.get('opportunity_count', 0) > row.get('rolling_30_day_avg', 0) * 2:
            return 'volume_spike'
        elif row.get('total_value', 0) > row.get('rolling_30_day_value', 0) * 2:
            return 'value_outlier'
        elif row.get('opportunity_count', 0) < row.get('rolling_30_day_avg', 0) * 0.5:
            return 'volume_drop'
        else:
            return 'pattern_anomaly'
    
    def store_trend_analysis(self, df: pd.DataFrame) -> bool:
        """
        Store trend analysis results in the database.
        
        Args:
            df: DataFrame with trend analysis results
            
        Returns:
            Boolean indicating success
        """
        try:
            # Prepare records for insertion
            records = []
            for index, row in df.iterrows():
                record = {
                    'analysis_date': index.date() if hasattr(index, 'date') else index,
                    'analysis_type': row.get('analysis_type', 'daily'),
                    'opportunity_count': int(row.get('opportunity_count', 0)),
                    'total_value': float(row.get('total_value', 0)),
                    'avg_value': float(row.get('avg_value', 0)),
                    'industry_breakdown': json.dumps(row.get('industry_breakdown', {})),
                    'region_breakdown': json.dumps(row.get('region_breakdown', {})),
                    'agency_breakdown': json.dumps(row.get('agency_breakdown', {})),
                    'is_anomaly': bool(row.get('is_anomaly', False)),
                    'anomaly_score': float(row.get('anomaly_score', 0)),
                    'anomaly_type': row.get('anomaly_type'),
                    'trending_keywords': json.dumps(row.get('trending_keywords', {})),
                    'rolling_7_day_avg': float(row.get('rolling_7_day_avg', 0)),
                    'rolling_30_day_avg': float(row.get('rolling_30_day_avg', 0)),
                    'year_over_year_change': float(row.get('yoy_opportunity_change', 0)),
                }
                records.append(record)
            
            if not records:
                logger.warning("No records to store")
                return True
            
            # Batch insert using raw SQL for better performance
            insert_sql = """
                INSERT INTO trend_analysis (
                    analysis_date, analysis_type, opportunity_count, total_value, avg_value,
                    industry_breakdown, region_breakdown, agency_breakdown,
                    is_anomaly, anomaly_score, anomaly_type, trending_keywords,
                    rolling_7_day_avg, rolling_30_day_avg, year_over_year_change
                ) VALUES (
                    :analysis_date, :analysis_type, :opportunity_count, :total_value, :avg_value,
                    :industry_breakdown, :region_breakdown, :agency_breakdown,
                    :is_anomaly, :anomaly_score, :anomaly_type, :trending_keywords,
                    :rolling_7_day_avg, :rolling_30_day_avg, :year_over_year_change
                )
                ON CONFLICT (analysis_date, analysis_type) 
                DO UPDATE SET
                    opportunity_count = EXCLUDED.opportunity_count,
                    total_value = EXCLUDED.total_value,
                    avg_value = EXCLUDED.avg_value,
                    industry_breakdown = EXCLUDED.industry_breakdown,
                    region_breakdown = EXCLUDED.region_breakdown,
                    agency_breakdown = EXCLUDED.agency_breakdown,
                    is_anomaly = EXCLUDED.is_anomaly,
                    anomaly_score = EXCLUDED.anomaly_score,
                    anomaly_type = EXCLUDED.anomaly_type,
                    trending_keywords = EXCLUDED.trending_keywords,
                    rolling_7_day_avg = EXCLUDED.rolling_7_day_avg,
                    rolling_30_day_avg = EXCLUDED.rolling_30_day_avg,
                    year_over_year_change = EXCLUDED.year_over_year_change,
                    updated_at = NOW()
            """
            
            db.session.execute(text(insert_sql), records)
            db.session.commit()
            
            logger.info(f"Successfully stored {len(records)} trend analysis records")
            return True
            
        except Exception as e:
            logger.error(f"Error storing trend analysis: {e}")
            db.session.rollback()
            return False
    
    def run_full_analysis(self, days_back: int = 90, 
                         analysis_types: List[str] = ['daily', 'weekly']) -> Dict[str, Any]:
        """
        Run complete time-series analysis pipeline.
        
        Args:
            days_back: Number of days to analyze
            analysis_types: Types of analysis to perform
            
        Returns:
            Dictionary with analysis results and metadata
        """
        try:
            start_time = datetime.now()
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Load data
            logger.info(f"Starting trend analysis for last {days_back} days")
            df = self.get_opportunities_dataframe(start_date=start_date)
            
            if df.empty:
                return {
                    'success': False,
                    'message': 'No data available for analysis',
                    'metadata': {'duration_seconds': 0}
                }
            
            results = {
                'success': True,
                'data_points': len(df),
                'date_range': {
                    'start': df.index.min().isoformat() if len(df) > 0 else None,
                    'end': df.index.max().isoformat() if len(df) > 0 else None
                },
                'analysis_results': {}
            }
            
            # Run analysis for each type
            for analysis_type in analysis_types:
                logger.info(f"Running {analysis_type} analysis")
                
                # Calculate aggregations
                agg_df = self.calculate_time_series_aggregations(df, analysis_type)
                
                if not agg_df.empty:
                    # Detect anomalies
                    agg_df = self.detect_anomalies(agg_df)
                    
                    # Store results
                    stored = self.store_trend_analysis(agg_df)
                    
                    # Summarize results
                    anomaly_count = agg_df['is_anomaly'].sum()
                    avg_score = agg_df['anomaly_score'].mean()
                    
                    results['analysis_results'][analysis_type] = {
                        'records_analyzed': len(agg_df),
                        'anomalies_detected': int(anomaly_count),
                        'avg_anomaly_score': float(avg_score),
                        'stored_successfully': stored
                    }
                else:
                    results['analysis_results'][analysis_type] = {
                        'records_analyzed': 0,
                        'anomalies_detected': 0,
                        'error': 'No aggregated data generated'
                    }
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results['metadata'] = {
                'duration_seconds': duration,
                'analysis_timestamp': end_time.isoformat(),
                'methods_used': ['isolation_forest', 'lof', 'statistical']
            }
            
            logger.info(f"Trend analysis completed in {duration:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"Error in full analysis pipeline: {e}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {'duration_seconds': 0}
            } 
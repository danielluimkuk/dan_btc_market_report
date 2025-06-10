# =============================================================================
# data_storage.py - Complete Enhanced Asset Data Storage
# =============================================================================

from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity
import os
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
from azure.common import AzureException

class DataStorage:
    def __init__(self):
        self.account_name = os.getenv('AZURE_STORAGE_ACCOUNT')
        self.account_key = os.getenv('AZURE_STORAGE_KEY')
        self.table_name = 'assetdata'
        self.alerts_table = 'alerthistory'
        self.health_table = 'systemhealth'
        self.monetary_table = 'monetarydata'  # NEW: Add monetary data table
        
        if self.account_name and self.account_key:
            self.table_service = TableService(
                account_name=self.account_name,
                account_key=self.account_key
            )
            self._ensure_tables_exist()
        else:
            logging.warning('Azure Storage credentials not configured')
            self.table_service = None
    
    def _ensure_tables_exist(self):
        """Ensure all required tables exist"""
        tables_to_create = [self.table_name, self.alerts_table, self.health_table, self.monetary_table]  # NEW: Add monetary table
        
        for table in tables_to_create:
            try:
                self.table_service.create_table(table)
                logging.info(f'Table {table} created or already exists')
            except AzureException as e:
                if 'TableAlreadyExists' not in str(e):
                    logging.error(f'Error creating table {table}: {str(e)}')
                else:
                    logging.info(f'Table {table} already exists')
            except Exception as e:
                logging.error(f'Unexpected error creating table {table}: {str(e)}')
    
    def store_daily_data(self, data: Dict) -> None:
        """Store daily asset data"""
        if not self.table_service:
            logging.warning('Storage not configured, skipping data storage')
            return
        
        try:
            date_key = datetime.utcnow().strftime('%Y-%m-%d')
            timestamp = datetime.utcnow().isoformat()
            
            # Store each asset's data
            successful_stores = 0
            failed_stores = 0
            
            for asset, asset_data in data['assets'].items():
                try:
                    if 'error' in asset_data:
                        # Store error information
                        self._store_error_data(asset, asset_data, date_key, timestamp)
                        failed_stores += 1
                        continue
                    
                    entity = Entity()
                    entity.PartitionKey = asset
                    entity.RowKey = date_key
                    entity.Timestamp = timestamp
                    entity.asset_type = asset_data.get('type', 'unknown')
                    entity.price = float(asset_data.get('price', 0))
                    entity.collection_success = True
                    
                    # Store indicators as JSON string
                    indicators = asset_data.get('indicators', {})
                    entity.indicators = json.dumps(indicators) if indicators else '{}'
                    
                    # Store metadata
                    metadata = asset_data.get('metadata', {})
                    entity.metadata = json.dumps(metadata) if metadata else '{}'
                    
                    # Store individual indicator values for easier querying
                    for indicator, value in indicators.items():
                        if isinstance(value, (int, float)):
                            setattr(entity, f'ind_{indicator}', float(value))
                    
                    # Use insert_or_replace to handle duplicates
                    self.table_service.insert_or_replace_entity(self.table_name, entity)
                    successful_stores += 1
                    
                    logging.info(f'Stored data for {asset}: ${entity.price:.2f}')
                    
                except Exception as e:
                    logging.error(f'Error storing data for {asset}: {str(e)}')
                    failed_stores += 1
            
            # Store summary information
            self._store_collection_summary(date_key, timestamp, successful_stores, failed_stores, data)
            
            logging.info(f'Data storage complete: {successful_stores} successful, {failed_stores} failed')
            
        except Exception as e:
            logging.error(f'Error in store_daily_data: {str(e)}')
            raise
    
    def _store_error_data(self, asset: str, asset_data: Dict, date_key: str, timestamp: str) -> None:
        """Store error information for failed collections"""
        try:
            entity = Entity()
            entity.PartitionKey = asset
            entity.RowKey = date_key
            entity.Timestamp = timestamp
            entity.asset_type = asset_data.get('type', 'unknown')
            entity.price = 0.0
            entity.collection_success = False
            entity.error_message = asset_data.get('error', 'Unknown error')
            entity.indicators = '{}'
            entity.metadata = json.dumps({'error_details': asset_data.get('error', 'Unknown error')})
            
            self.table_service.insert_or_replace_entity(self.table_name, entity)
            
        except Exception as e:
            logging.error(f'Error storing error data for {asset}: {str(e)}')
    
    def _store_collection_summary(self, date_key: str, timestamp: str, successful: int, failed: int, data: Dict) -> None:
        """Store daily collection summary"""
        try:
            entity = Entity()
            entity.PartitionKey = 'SYSTEM'
            entity.RowKey = f'SUMMARY_{date_key}'
            entity.Timestamp = timestamp
            entity.successful_collections = successful
            entity.failed_collections = failed
            entity.total_assets = successful + failed
            entity.collection_time = timestamp
            entity.function_runtime = 'azure_function'  # Could be enhanced with actual runtime info
            
            self.table_service.insert_or_replace_entity(self.health_table, entity)
            
        except Exception as e:
            logging.error(f'Error storing collection summary: {str(e)}')
    
    def get_historical_data(self, asset: str, days: int = 7) -> List[Dict]:
        """Get historical data for an asset"""
        if not self.table_service:
            logging.warning('Storage not configured, returning empty data')
            return []
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Query with date range filter
            date_filter = self._build_date_range_filter(start_date, end_date)
            partition_filter = f"PartitionKey eq '{asset}'"
            combined_filter = f"{partition_filter} and {date_filter}"
            
            entities = self.table_service.query_entities(
                self.table_name,
                filter=combined_filter,
                select='RowKey,Timestamp,price,indicators,metadata,collection_success'
            )
            
            historical_data = []
            for entity in entities:
                try:
                    data_point = {
                        'date': entity.RowKey,
                        'timestamp': entity.Timestamp,
                        'price': float(entity.price) if entity.price else 0.0,
                        'success': getattr(entity, 'collection_success', True),
                        'indicators': json.loads(entity.indicators) if hasattr(entity, 'indicators') and entity.indicators else {},
                        'metadata': json.loads(entity.metadata) if hasattr(entity, 'metadata') and entity.metadata else {}
                    }
                    historical_data.append(data_point)
                except Exception as e:
                    logging.warning(f'Error parsing historical data point: {str(e)}')
                    continue
            
            # Sort by date (most recent first)
            historical_data.sort(key=lambda x: x['date'], reverse=True)
            
            logging.info(f'Retrieved {len(historical_data)} historical data points for {asset}')
            return historical_data
            
        except Exception as e:
            logging.error(f'Error retrieving historical data for {asset}: {str(e)}')
            return []
    
    def _build_date_range_filter(self, start_date: datetime, end_date: datetime) -> str:
        """Build OData filter for date range"""
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        return f"RowKey ge '{start_str}' and RowKey le '{end_str}'"
    
    def get_latest_data(self, asset: str) -> Optional[Dict]:
        """Get the most recent data for an asset"""
        historical_data = self.get_historical_data(asset, days=1)
        return historical_data[0] if historical_data else None
    
    def store_alert_history(self, alerts: List[Dict]) -> None:
        """Store alert history"""
        if not self.table_service or not alerts:
            return
        
        try:
            timestamp = datetime.utcnow()
            date_key = timestamp.strftime('%Y-%m-%d')
            
            for i, alert in enumerate(alerts):
                entity = Entity()
                entity.PartitionKey = alert.get('asset', 'UNKNOWN')
                entity.RowKey = f"{date_key}_{timestamp.strftime('%H%M%S')}_{i:03d}"
                entity.Timestamp = timestamp.isoformat()
                entity.alert_type = alert.get('type', 'unknown')
                entity.message = alert.get('message', '')
                entity.severity = alert.get('severity', 'medium')
                entity.date_created = date_key
                
                # Add any additional alert data
                for key, value in alert.items():
                    if key not in ['asset', 'type', 'message', 'severity'] and isinstance(value, (str, int, float, bool)):
                        setattr(entity, f'data_{key}', value)
                
                self.table_service.insert_entity(self.alerts_table, entity)
            
            logging.info(f'Stored {len(alerts)} alerts to history')
            
        except Exception as e:
            logging.error(f'Error storing alert history: {str(e)}')
    
    def get_alert_history(self, asset: str = None, days: int = 30) -> List[Dict]:
        """Get alert history"""
        if not self.table_service:
            return []
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            date_filter = self._build_date_range_filter(start_date, end_date)
            
            if asset:
                filter_query = f"PartitionKey eq '{asset}' and {date_filter}"
            else:
                filter_query = date_filter
            
            entities = self.table_service.query_entities(self.alerts_table, filter=filter_query)
            
            alerts = []
            for entity in entities:
                alert = {
                    'asset': entity.PartitionKey,
                    'timestamp': entity.Timestamp,
                    'type': getattr(entity, 'alert_type', 'unknown'),
                    'message': getattr(entity, 'message', ''),
                    'severity': getattr(entity, 'severity', 'medium'),
                    'date': getattr(entity, 'date_created', 'unknown')
                }
                alerts.append(alert)
            
            return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logging.error(f'Error retrieving alert history: {str(e)}')
            return []
    
    def get_data_analytics(self, asset: str, days: int = 30) -> Dict:
        """Get analytics data for an asset"""
        try:
            historical_data = self.get_historical_data(asset, days)
            
            if not historical_data:
                return {'error': 'No data available'}
            
            # Convert to pandas for easier analysis
            df = pd.DataFrame(historical_data)
            
            # Basic statistics
            analytics = {
                'asset': asset,
                'period_days': days,
                'total_data_points': len(df),
                'successful_collections': len(df[df['success'] == True]),
                'failed_collections': len(df[df['success'] == False]),
                'data_quality': (len(df[df['success'] == True]) / len(df)) * 100 if len(df) > 0 else 0
            }
            
            # Price analytics (only for successful data points)
            successful_df = df[df['success'] == True]
            if len(successful_df) > 0:
                prices = successful_df['price'].astype(float)
                analytics.update({
                    'price_current': float(prices.iloc[0]) if len(prices) > 0 else 0,
                    'price_min': float(prices.min()),
                    'price_max': float(prices.max()),
                    'price_avg': float(prices.mean()),
                    'price_std': float(prices.std()) if len(prices) > 1 else 0,
                    'price_change_pct': ((prices.iloc[0] - prices.iloc[-1]) / prices.iloc[-1] * 100) if len(prices) > 1 else 0
                })
            
            # Indicator analytics
            if len(successful_df) > 0:
                indicators_analysis = self._analyze_indicators(successful_df)
                analytics['indicators'] = indicators_analysis
            
            return analytics
            
        except Exception as e:
            logging.error(f'Error generating analytics for {asset}: {str(e)}')
            return {'error': str(e)}
    
    def _analyze_indicators(self, df: pd.DataFrame) -> Dict:
        """Analyze indicators from historical data"""
        indicators_analysis = {}
        
        try:
            for _, row in df.iterrows():
                if row['indicators']:
                    for indicator, value in row['indicators'].items():
                        if isinstance(value, (int, float)):
                            if indicator not in indicators_analysis:
                                indicators_analysis[indicator] = []
                            indicators_analysis[indicator].append(float(value))
            
            # Calculate statistics for each indicator
            for indicator, values in indicators_analysis.items():
                if values:
                    indicators_analysis[indicator] = {
                        'current': values[0] if values else 0,
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'count': len(values)
                    }
        
        except Exception as e:
            logging.error(f'Error analyzing indicators: {str(e)}')
        
        return indicators_analysis
    
    def get_system_health(self, days: int = 7) -> Dict:
        """Get system health metrics"""
        if not self.table_service:
            return {'error': 'Storage not configured'}
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            date_filter = self._build_date_range_filter(start_date, end_date)
            partition_filter = "PartitionKey eq 'SYSTEM'"
            combined_filter = f"{partition_filter} and {date_filter}"
            
            entities = self.table_service.query_entities(
                self.health_table,
                filter=combined_filter
            )
            
            health_data = []
            for entity in entities:
                health_point = {
                    'date': entity.RowKey.replace('SUMMARY_', ''),
                    'successful_collections': getattr(entity, 'successful_collections', 0),
                    'failed_collections': getattr(entity, 'failed_collections', 0),
                    'total_assets': getattr(entity, 'total_assets', 0),
                    'collection_time': getattr(entity, 'collection_time', ''),
                    'success_rate': (getattr(entity, 'successful_collections', 0) / 
                                   max(getattr(entity, 'total_assets', 1), 1)) * 100
                }
                health_data.append(health_point)
            
            # Calculate overall health metrics
            if health_data:
                total_collections = sum(h['total_assets'] for h in health_data)
                successful_collections = sum(h['successful_collections'] for h in health_data)
                
                health_summary = {
                    'period_days': days,
                    'total_collection_runs': len(health_data),
                    'total_asset_collections': total_collections,
                    'successful_collections': successful_collections,
                    'failed_collections': total_collections - successful_collections,
                    'overall_success_rate': (successful_collections / max(total_collections, 1)) * 100,
                    'daily_health': sorted(health_data, key=lambda x: x['date'], reverse=True)
                }
            else:
                health_summary = {
                    'period_days': days,
                    'total_collection_runs': 0,
                    'message': 'No health data available for the specified period'
                }
            
            return health_summary
            
        except Exception as e:
            logging.error(f'Error retrieving system health: {str(e)}')
            return {'error': str(e)}
    
    def cleanup_old_data(self, retention_days: int = 90) -> Dict:
        """Clean up old data beyond retention period"""
        if not self.table_service:
            return {'error': 'Storage not configured'}
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            # Query old data
            filter_query = f"RowKey lt '{cutoff_str}'"
            
            cleanup_results = {
                'cutoff_date': cutoff_str,
                'tables_processed': 0,
                'entities_deleted': 0,
                'errors': []
            }
            
            # Clean up each table
            tables_to_clean = [self.table_name, self.alerts_table, self.health_table]
            
            for table in tables_to_clean:
                try:
                    entities = self.table_service.query_entities(table, filter=filter_query, select='PartitionKey,RowKey')
                    
                    deleted_count = 0
                    for entity in entities:
                        try:
                            self.table_service.delete_entity(table, entity.PartitionKey, entity.RowKey)
                            deleted_count += 1
                        except Exception as e:
                            cleanup_results['errors'].append(f'Error deleting entity from {table}: {str(e)}')
                    
                    cleanup_results['entities_deleted'] += deleted_count
                    cleanup_results['tables_processed'] += 1
                    
                    logging.info(f'Cleaned up {deleted_count} old entities from {table}')
                    
                except Exception as e:
                    cleanup_results['errors'].append(f'Error cleaning table {table}: {str(e)}')
            
            logging.info(f'Cleanup complete: {cleanup_results["entities_deleted"]} entities deleted from {cleanup_results["tables_processed"]} tables')
            return cleanup_results
            
        except Exception as e:
            logging.error(f'Error in cleanup_old_data: {str(e)}')
            return {'error': str(e)}
    
    def export_data_to_csv(self, asset: str, days: int = 30, output_path: str = None) -> str:
        """Export asset data to CSV file"""
        try:
            historical_data = self.get_historical_data(asset, days)
            
            if not historical_data:
                raise Exception(f'No data available for {asset}')
            
            # Flatten the data for CSV export
            flattened_data = []
            for data_point in historical_data:
                row = {
                    'date': data_point['date'],
                    'timestamp': data_point['timestamp'],
                    'price': data_point['price'],
                    'collection_success': data_point['success']
                }
                
                # Add indicators as separate columns
                for indicator, value in data_point.get('indicators', {}).items():
                    row[f'indicator_{indicator}'] = value
                
                flattened_data.append(row)
            
            # Create DataFrame and export
            df = pd.DataFrame(flattened_data)
            
            if output_path is None:
                output_path = f'{asset}_data_{datetime.utcnow().strftime("%Y%m%d")}.csv'
            
            df.to_csv(output_path, index=False)
            
            logging.info(f'Exported {len(flattened_data)} data points for {asset} to {output_path}')
            return output_path
            
        except Exception as e:
            logging.error(f'Error exporting data for {asset}: {str(e)}')
            raise

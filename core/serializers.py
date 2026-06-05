"""
Serialization and data transformation utilities
"""

import json
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from enum import Enum


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for common types"""
    
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


class DataSerializer:
    """Serializes and deserializes data"""
    
    @staticmethod
    def to_json(data: Any, indent: int = 2) -> str:
        """Convert data to JSON string"""
        return json.dumps(data, cls=JSONEncoder, indent=indent)
    
    @staticmethod
    def from_json(json_str: str) -> Any:
        """Parse JSON string to data"""
        return json.loads(json_str)
    
    @staticmethod
    def serialize_model(model_instance, fields: Optional[List[str]] = None) -> Dict:
        """Serialize Django model instance"""
        data = {}
        
        if fields:
            for field in fields:
                value = getattr(model_instance, field, None)
                data[field] = DataSerializer._serialize_value(value)
        else:
            for field in model_instance._meta.fields:
                value = getattr(model_instance, field.name, None)
                data[field.name] = DataSerializer._serialize_value(value)
        
        return data
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize individual value"""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, Enum):
            return value.value
        elif hasattr(value, '__dict__'):
            return str(value)
        return value


class DataTransformer:
    """Transforms data between formats"""
    
    @staticmethod
    def flatten_dict(nested_dict: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in nested_dict.items():
            new_key = f'{parent_key}{sep}{k}' if parent_key else k
            if isinstance(v, dict):
                items.extend(DataTransformer.flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v, cls=JSONEncoder)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    @staticmethod
    def unflatten_dict(flat_dict: Dict, sep: str = '_') -> Dict:
        """Unflatten dictionary"""
        result = {}
        for key, value in flat_dict.items():
            parts = key.split(sep)
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        return result
    
    @staticmethod
    def merge_dicts(*dicts: Dict) -> Dict:
        """Merge multiple dictionaries"""
        result = {}
        for d in dicts:
            result.update(d)
        return result
    
    @staticmethod
    def filter_dict(data: Dict, keys: List[str]) -> Dict:
        """Filter dictionary to only include specified keys"""
        return {k: v for k, v in data.items() if k in keys}
    
    @staticmethod
    def exclude_dict(data: Dict, keys: List[str]) -> Dict:
        """Filter dictionary excluding specified keys"""
        return {k: v for k, v in data.items() if k not in keys}


class ListTransformer:
    """Transforms lists and collections"""
    
    @staticmethod
    def chunk_list(items: List, chunk_size: int) -> List[List]:
        """Split list into chunks"""
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
    
    @staticmethod
    def unique_list(items: List, key_func=None) -> List:
        """Get unique items from list"""
        if key_func:
            seen = set()
            result = []
            for item in items:
                key = key_func(item)
                if key not in seen:
                    seen.add(key)
                    result.append(item)
            return result
        return list(dict.fromkeys(items))
    
    @staticmethod
    def group_by(items: List, key_func) -> Dict[Any, List]:
        """Group list items by key function"""
        groups = {}
        for item in items:
            key = key_func(item)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups
    
    @staticmethod
    def sort_by_multiple(items: List, sort_specs: List[Tuple]) -> List:
        """Sort list by multiple criteria"""
        for key_func, reverse in reversed(sort_specs):
            items = sorted(items, key=key_func, reverse=reverse)
        return items


class CSVTransformer:
    """Transforms data to/from CSV format"""
    
    @staticmethod
    def list_to_csv(data: List[Dict], delimiter: str = ',') -> str:
        """Convert list of dicts to CSV string"""
        if not data:
            return ''
        
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys(), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    
    @staticmethod
    def csv_to_list(csv_string: str, delimiter: str = ',') -> List[Dict]:
        """Convert CSV string to list of dicts"""
        import csv
        from io import StringIO
        
        reader = csv.DictReader(StringIO(csv_string), delimiter=delimiter)
        return list(reader)
    
    @staticmethod
    def queryset_to_csv(queryset, fields: List[str], delimiter: str = ',') -> str:
        """Convert Django queryset to CSV"""
        data = []
        for obj in queryset:
            row = {}
            for field in fields:
                value = getattr(obj, field, '')
                row[field] = DataSerializer._serialize_value(value)
            data.append(row)
        return CSVTransformer.list_to_csv(data, delimiter)


class BulkOperationHelper:
    """Helper for bulk operations"""
    
    @staticmethod
    def bulk_create_from_list(model_class, data_list: List[Dict], batch_size: int = 1000):
        """Bulk create model instances"""
        instances = [model_class(**data) for data in data_list]
        return model_class.objects.bulk_create(instances, batch_size=batch_size)
    
    @staticmethod
    def bulk_update_from_list(model_class, data_list: List[Dict], id_field: str = 'id', batch_size: int = 1000):
        """Bulk update model instances"""
        instances = []
        for data in data_list:
            obj_id = data.pop(id_field)
            instance = model_class(id=obj_id, **data)
            instances.append(instance)
        
        fields_to_update = list(data_list[0].keys()) if data_list else []
        return model_class.objects.bulk_update(instances, fields=fields_to_update, batch_size=batch_size)


class ExcelTransformer:
    """Transforms data to/from Excel format (requires openpyxl)"""
    
    @staticmethod
    def list_to_excel_bytes(data: List[Dict], sheet_name: str = 'Sheet1') -> bytes:
        """Convert list of dicts to Excel bytes"""
        try:
            import openpyxl
            from io import BytesIO
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = sheet_name
            
            if data:
                headers = list(data[0].keys())
                ws.append(headers)
                
                for row_data in data:
                    ws.append([row_data.get(h) for h in headers])
            
            output = BytesIO()
            wb.save(output)
            return output.getvalue()
        except ImportError:
            raise ImportError('openpyxl is required for Excel transformation')
    
    @staticmethod
    def queryset_to_excel_bytes(queryset, fields: List[str], sheet_name: str = 'Sheet1') -> bytes:
        """Convert Django queryset to Excel bytes"""
        data = []
        for obj in queryset:
            row = {}
            for field in fields:
                value = getattr(obj, field, '')
                row[field] = DataSerializer._serialize_value(value)
            data.append(row)
        return ExcelTransformer.list_to_excel_bytes(data, sheet_name)


# Type hints for transformers
from typing import Tuple

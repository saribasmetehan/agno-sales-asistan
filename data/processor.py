import json
import chromadb
from chromadb.utils import embedding_functions

class VectorDBProcessor:
    """Sales playbook için Türkçe BERT embedding kullanan basit vector DB processor"""
    
    def __init__(self, json_path: str, collection_name: str = "sales_playbook"):
        self.json_path = json_path
        
        self.client = chromadb.Client()
        
        # Try to use Turkish BERT embeddings, fallback to default if not available
        try:
            self.embedding_function = embedding_functions.FastEmbedEmbeddingFunction(
                model_name="emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"
            )
        except Exception as e:
            print(f"Warning: Failed to load Turkish BERT, falling back to default: {e}")
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
    
    def load_and_embed(self):
        """JSON'dan playbook verilerini yükler ve embedding'lerini oluşturur"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []  # Embed edilecek textler (rule_text)
        metadatas = []  # Diğer bilgiler
        ids = []        # Unique ID'ler
        
        for rule in data:
            # rule_text alanını embedding için kullan
            documents.append(rule['rule_text'])
            
            metadata = {
                'rule_id': rule['rule_id'],
                'rule_category': rule['rule_category'],
                'priority_level': rule['priority_level'],
                'action_type': rule['action_type'],
                'approval_required': str(rule['approval_required']),
            }
            
            if rule.get('recommended_product'):
                metadata['recommended_product'] = rule['recommended_product']
            
            if rule.get('industry_filter'):
                metadata['industry_filter'] = ','.join(rule['industry_filter'])
            
            if rule.get('spend_threshold_min') is not None:
                metadata['spend_threshold_min'] = rule['spend_threshold_min']
            
            if rule.get('spend_threshold_max') is not None:
                metadata['spend_threshold_max'] = rule['spend_threshold_max']
            
            metadatas.append(metadata)
            ids.append(rule['rule_id'])
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ {len(documents)} adet kural başarıyla embed edildi!")
        return len(documents)
    
    def get_collection_info(self):
        count = self.collection.count()
        print(f"📊 Collection: {self.collection.name}")
        print(f"📊 Toplam kayıt: {count}")
        return count
    
    def playbook_query(self, query_text: str, n_results: int = 1, filter_dict: dict = None):
        """
        LLM tool'ları için optimize edilmiş sorgu fonksiyonu
        
        Args:
            query_text: Sorgu metni
            n_results: Kaç sonuç döndürülecek
            filter_dict: Metadata filtreleme (örn: {"rule_category": "budget_threshold"})
        
        Returns:
            JSON string: Formatlanmış sonuçlar
        """
        where_clause = None
        if filter_dict and len(filter_dict) > 0:
            if len(filter_dict) == 1:
                # Tek koşul ise direkt kullan
                where_clause = filter_dict
            else:
                # Birden fazla koşul varsa $and operatörü ile sarmala
                where_clause = {
                    "$and": [
                        {key: value} for key, value in filter_dict.items()
                    ]
                }
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_clause
        )
        
        formatted_results = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                result_item = {
                    'rule_id': metadata['rule_id'],
                    'rule_category': metadata['rule_category'],
                    'rule_text': results['documents'][0][i],
                    'priority_level': metadata['priority_level'],
                    'action_type': metadata['action_type'],
                    'approval_required': metadata['approval_required'] == 'True',
                    'similarity_score': round(1 - results['distances'][0][i], 4),
                }
                
                if 'recommended_product' in metadata:
                    result_item['recommended_product'] = metadata['recommended_product']
                if 'industry_filter' in metadata:
                    result_item['industry_filter'] = metadata['industry_filter'].split(',')
                if 'spend_threshold_min' in metadata:
                    result_item['spend_threshold_min'] = metadata['spend_threshold_min']
                if 'spend_threshold_max' in metadata:
                    result_item['spend_threshold_max'] = metadata['spend_threshold_max']

                formatted_results.append(result_item)
        
        return json.dumps(formatted_results, ensure_ascii=False, indent=2)

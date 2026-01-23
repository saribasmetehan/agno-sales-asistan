import json
from tools.utils import call_llm
from prompts.prompt import system_prompt, guardrail_prompt
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from pathlib import Path
from data.processor import VectorDBProcessor

# Initialize processor for playbook queries
PLAYBOOK_PATH = Path(__file__).parent.parent / "data" / "sales_playbook.json"
processor = VectorDBProcessor(json_path=str(PLAYBOOK_PATH))

# Eğer collection boşsa, verileri yükle
if processor.collection.count() == 0:
    print("[INFO] Vektor DB bos, playbook yukleniyor...")
    processor.load_and_embed()
else:
    print(f"[INFO] Vektor DB hazir: {processor.collection.count()} kural mevcut")

def playbook_search(query_text: str, n_results: int = 1, filter_dict: dict = None):
        """
        Satış playbook'unda (oyun kitabı) anlamsal arama yapar ve ilgili kuralları getirir.
        
        Bu tool, satış stratejilerini, kuralları, indirim politikalarını ve sektör bazlı önerileri bulmak için kullanılır.
        Playbook şu alanları içerir:
        - rule_id: Benzersiz kural ID'si (örn: RULE_001, RULE_002)
        - rule_category: Kural kategorisi (channel_strategy, budget_threshold, product_recommendation, pricing_policy, compliance)
        - rule_text: Kuralın detaylı açıklaması ve strateji metni
        - recommended_product: Önerilen ürün veya hizmet (örn: "In-Store Digital Display", "Mobile App Banners")
        - priority_level: Öncelik seviyesi (high, medium, critical)
        - action_type: Aksiyon tipi (recommend, require_approval, mandatory, avoid)
        - approval_required: Onay gerekip gerekmediği (true/false)
        - industry_filter: İlgili sektörler (örn: FMCG, Finance, Healthcare, Electronics, Technology, All)
        - spend_threshold_min: Minimum harcama eşiği (varsa)
        - spend_threshold_max: Maximum harcama eşiği (varsa)
        
        Args:
            query_text: Aranacak strateji veya durum ile ilgili doğal dil sorgusu (örn: "FMCG sektörü için strateji nedir?")
            n_results: Döndürülecek sonuç sayısı (Varsayılan: 1)
            filter_dict: Metadata alanlarına göre filtreleme (örn: {"rule_category": "budget_threshold"})
        
        Returns:
            JSON string: Bulunan playbook kurallarının detaylı listesi. HER ZAMAN TÜM FIELD'LARI bildirmek zorundasın!
        """
        return processor.playbook_query(query_text, n_results, filter_dict)



def check_guardrails(query: str) -> str:
    f"""
    Satış Asistanı için Güvenlik Kontrolü Tool'udur.
    Bu tool her kullanıcı sorgusunun güvenli olup olmadığını kontrol eder. Her zaman ilk çalışması gereken tool'dur.
    
    """
    try:
        result = call_llm(
            user_prompt=query,
            system_prompt=guardrail_prompt,
        )
        return result.strip()
    except Exception as e:
        return f"UNSAFE: Error: {str(e)}"


PlaybookAgent = Agent(
    name="Playbook Agent",
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file=str(Path(__file__).parent.parent / "data" / "agno_shared.db")),
    tools=[
        playbook_search,
        check_guardrails,
    ],
    instructions=system_prompt,
    add_history_to_context=True,
    markdown=True,
)
import sqlite3
import json
from pathlib import Path
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from prompts.prompt import sql_prompt

DB_PATH = Path(__file__).parent.parent / "data" / "crm.db"

def get_schema() -> dict:
    """
    CRM veritabanının şemasını getirir.
    run_sql_query tool'undan önce  bu tool'u çağırarak CRM veritabanının şemasını öğrenmeniz gerekiyor.
    
    Returns:
        Tablo ve sütun detaylarını içeren şema bilgisi
    """
    return {
        "table": "customers",
        "columns": [
            {"name": "client_id", "type": "TEXT", "description": "Müşteri ID"},
            {"name": "client_name", "type": "TEXT", "description": "Müşteri adı"},
            {"name": "industry", "type": "TEXT", "description": "Sektör"},
            {"name": "total_spend_ytd", "type": "INTEGER", "description": "Bu yılki toplam harcama"},
            {"name": "last_meeting_date", "type": "TEXT", "description": "Son toplantı tarihi"},
            {"name": "account_manager", "type": "TEXT", "description": "Hesap yöneticisi"},
            {"name": "region", "type": "TEXT", "description": "Bölge"},
            {"name": "company_size", "type": "TEXT", "description": "Şirket büyüklüğü"},
            {"name": "contract_value", "type": "INTEGER", "description": "Sözleşme değeri"},
            {"name": "contract_status", "type": "TEXT", "description": "Sözleşme durumu"},
            {"name": "products_used", "type": "TEXT", "description": "Kullanılan ürünler"}
        ]
    }


def run_sql_query(query: str) -> str:
    """
    CRM veritabanında SQL sorgusu çalıştırır.
    Önce get_schema tool'u ile şemayı öğrenip, buna göre SQL sorgusu oluşturun.
    
    Args:
        query: Çalıştırılacak SELECT sorgusu
               (örn: "SELECT * FROM customers WHERE region = 'Istanbul'")
    
    Returns:
        JSON string: Sorgu sonuçları
    """
    try:
        # Güvenlik: Sadece SELECT
        if not query.strip().upper().startswith("SELECT"):
            return json.dumps({"error": "Sadece SELECT sorguları desteklenir"}, ensure_ascii=False)
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(query)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        
        return json.dumps(results, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


SQLAgent = Agent(
    name="SQL Agent",
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file=str(Path(__file__).parent.parent / "data" / "agno_shared.db")),
    tools=[
        get_schema,
        run_sql_query,
    ],
    instructions=sql_prompt,
    add_history_to_context=True,
    markdown=True,
)


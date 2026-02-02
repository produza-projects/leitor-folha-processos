import threading
import os

class DatabaseCache:
    def __init__(self):
        self.cache = {}
        self.last_modified = None
        self.lock = threading.Lock()
    
    def load_database(self, path: str):
        try:
            current_modified = os.path.getmtime(path)
            
            if self.last_modified is None or current_modified > self.last_modified:
                with self.lock:
                    self.cache.clear()
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for linha in f:
                            if ";" not in linha:
                                continue
                            partes = linha.strip().split(";", 1)
                            if len(partes) != 2:
                                continue
                            codigo, caminho = partes
                            self.cache[codigo.strip()] = caminho.strip()
                    self.last_modified = current_modified
                    print(f"✓ Database recarregado: {len(self.cache)} registros")
        except Exception as e:
            print(f"✗ Erro ao carregar database: {e}")
    
    def buscar(self, serial: str) -> str | None:
        return self.cache.get(serial)
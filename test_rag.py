from rag import indexar_todos, buscar_semantico

print("=" * 50)
print("Indexando apuntes existentes en ChromaDB...")
print("=" * 50)
indexar_todos()

print("\n" + "=" * 50)
print("TEST 1: Buscar 'encriptacion y manejo de strings'")
print("=" * 50)
buscar_semantico("encriptacion y manejo de strings")

print("\n" + "=" * 50)
print("TEST 2: Buscar 'estructuras de datos con punteros'")
print("=" * 50)
buscar_semantico("estructuras de datos con punteros")

print("\n" + "=" * 50)
print("TEST 3: Buscar 'resumen de pilas y colas'")
print("=" * 50)
buscar_semantico("resumen de pilas y colas")

print("\nTests de búsqueda semántica completados.")

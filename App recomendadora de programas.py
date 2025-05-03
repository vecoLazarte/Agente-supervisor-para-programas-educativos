import os
import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.tools import tool
from langchain.agents import load_tools
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.sql_database import SQLDatabase
import uuid

# Cargar claves API y URI de BD
with open("APPI OPENAI.txt") as archivo:
    apikey_OPENAI = archivo.read()
os.environ["OPENAI_API_KEY"] = apikey_OPENAI

with open("postgrest.txt") as archivo:
    uribd = archivo.read()

with open("APPI TAVILY.txt") as archivo:
    apikey_TAVILY = archivo.read()
os.environ["TAVILY_API_KEY"] = apikey_TAVILY

# Instancias de herramientas y modelo
model = ChatOpenAI(verbose=True, temperature=0, model="gpt-4")
tavily_tool = TavilySearchResults(max_results=5)
arxiv_tool = load_tools(["arxiv"], llm=model)[0]
db_data = SQLDatabase.from_uri(uribd)
memory = MemorySaver()

# Herramientas personalizadas
@tool
def get_schema() -> str:
  "Herramienta para recuperar el esquema de la base de datos, solo de las tablas de ingresos y gastos"
  return db_data.get_table_info()

promptsql = ChatPromptTemplate.from_template("""
    Basándote únicamente en las tablas ingresos y gastos del siguiente esquema, genera una consulta SQL para conocer el presupuesto mensual promedio que es sumar todos los ingresos y restarlos con los gastos y finalmente dividirlo entre 12: {schema}
    """)

sqlchain = (
    promptsql
    | model.bind(stop=["\nSQLResult:"])
    | StrOutputParser()
)

@tool
def generar_sql(table_schema: str, question: str) -> str:
    """Genera una consulta SQL a partir del esquema, solo puedes usar la tabla ingresos y gastos """
    return sqlchain.invoke({"schema": table_schema})


@tool
def run_query(query:str) -> str:
    """Herramienta que ejecuta una consulta SQL en la base de datos"""
    return db_data.run(query)

@tool
def tendencias_tool(area: str) -> str:
    """Genera 2 subcampos relevantes para un área de interés utilizando Tavily."""
    # Construir una query de texto directamente
    consulta = f"Identifica 2 subcampos emergentes en el área de {area} utilizando fuentes como Tavily"
    
    # Pasar la consulta en el formato esperado por TavilySearchResults
    resultados = tavily_tool.invoke({"query": consulta})
    
    # Asegúrate de que los resultados sean procesados correctamente
    if isinstance(resultados, list):
        subcampos = [res['title'] for res in resultados if isinstance(res, dict)]
        return "\n".join(subcampos)  # Devuelve los títulos de los subcampos como texto plano
    return "No se encontraron resultados relevantes."


@tool
def generar_programas(lista_tendencias: str) -> str:
    """Genera programas educativos recomendados basados en las tendencias proporcionadas."""
    
    # Formar la consulta con las tendencias proporcionadas
    consulta = f"""
    Basándote únicamente en las tendencias de la siguiente lista {lista_tendencias}, recomienda 1 programa educativo actual para cada subcampo emergente detectado, utilizando fuentes como edX, Coursera, universidades acreditadas, escuelas técnicas, y otras plataformas educativas reconocidas.
    Si no se conoce la duración del curso indica cuál es la duración promedio de un programa como ese.
    Si no conoce el costo mensual indica cuál es el costo mensual promedio de un programa educativo como ese.
    La salida debe ser [subcampo 1: [[programa, institución que lo ofrece, costo mensual, duración del curso], subcampo 2: [programa, institución que lo ofrece, costo mensual, duración del curso]]
    Evita programas genéricos o desactualizados.
    """
    
    # Intentar invocar Tavily para obtener los resultados
    try:
        resultados = tavily_tool.invoke({"query": consulta})
        
        # Verificar si los resultados son válidos
        if isinstance(resultados, list):
            # Procesar los resultados en el formato adecuado
            programas = [res['title'] for res in resultados if isinstance(res, dict)]
            return "\n".join(programas)  # Devolver los títulos de los programas
        else:
            return "No se encontraron programas educativos relevantes para las tendencias dadas."
    except Exception as e:
        # Si ocurre un error, devolver un mensaje adecuado
        return f"Error al consultar los programas educativos: {str(e)}"


def calcular_si_alcanza_presupuesto(costo_mensual: float, presupuesto_mensual: float) -> str:
    if presupuesto_mensual >= costo_mensual:
        return f"✅ Puede pagar el programa. Costo mensual: ${costo_mensual:.2f}, Presupuesto mensual: ${presupuesto_mensual:.2f}."
    else:
        return f"❌ No puede pagar el programa. Costo mensual: ${costo_mensual:.2f}, Presupuesto mensual: ${presupuesto_mensual:.2f}."

def convertir_moneda(monto: float, tasa_cambio: float) -> float:
    return monto * tasa_cambio

def obtener_tasa_cambio(moneda_origen: str, moneda_destino: str) -> float:
    tasas_simuladas = {
        ("USD", "PEN"): 3.7,
        ("EUR", "PEN"): 4.1,
    }
    return tasas_simuladas.get((moneda_origen.upper(), moneda_destino.upper()), 1.0)

@tool
def calcular_si_alcanza_presupuesto_tool(costo_mensual: float, presupuesto_mensual: float) -> str:
    """Compara el costo mensual de un programa con el presupuesto promedio mensual del usuario. 
    Devuelve un mensaje indicando si el usuario puede o no pagar el programa."""
    return calcular_si_alcanza_presupuesto(costo_mensual, presupuesto_mensual)

@tool
def convertir_moneda_tool(monto: float, tasa_cambio: float) -> float:
    """Convierte una cantidad monetaria usando una tasa de cambio dada. 
    Útil para convertir el precio del programa a la moneda del usuario."""
    return convertir_moneda(monto, tasa_cambio)

@tool
def obtener_tasa_cambio_tool(moneda_origen: str, moneda_destino: str) -> float:
    """Obtiene la tasa de cambio entre dos monedas."""
    return obtener_tasa_cambio(moneda_origen, moneda_destino)

# Toolkit y agente
tolkit = [
    get_schema,
    generar_sql,
    run_query,
    tendencias_tool,
    generar_programas,
    calcular_si_alcanza_presupuesto_tool,
    convertir_moneda_tool,
    obtener_tasa_cambio_tool
]

prompt_agente = ChatPromptTemplate.from_messages([
    ("system", """
    Eres un agente experto en recomendar programas educativos...
    """),
    ("human", "{messages}"),
])

agent = create_react_agent(model, tolkit, checkpointer=memory, prompt=prompt_agente)

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Chester Consultores", layout="centered")
st.title("🎓 Chester Consultores")
st.write("Disfruta del apoyo de tus consultores en tu vida post universitaria.")

# Inicializar historial de conversación
if 'contexto' not in st.session_state:
    st.session_state.contexto = []

# Entrada de usuario
mensaje = st.text_input("Escribe tu mensaje aquí:")

def enviar_mensajes(historial):
    # Convertir historial en formato que el agente espera
    full_conversation = "\n".join(
        [f"{m['role']}: {m['content']}" for m in historial]
    )
    thread_id = "usuario_1"

    # Invocar al agente
    resultado = agent.invoke(
        {"messages": full_conversation},
        config={"thread_id": thread_id}
    )

    # Mostrar el resultado para depurar
    st.write("Resultado del agente:", resultado)

    # Retornar el mensaje correcto
    if isinstance(resultado, dict):
        # Intenta acceder a posibles claves útiles
        for clave in ["output", "content", "response", "respuesta"]:
            if clave in resultado:
                return resultado[clave]
        # Si no encuentra nada, devuelve el dict completo como string
        return str(resultado)
    else:
        # Si el resultado no es un diccionario, simplemente lo devuelve
        return str(resultado)


if st.button("Enviar"):
    if mensaje:
        st.session_state.contexto.append({'role': 'user', 'content': mensaje})
        respuesta = enviar_mensajes(st.session_state.contexto)
        st.session_state.contexto.append({'role': 'assistant', 'content': respuesta})
        st.success(respuesta)
    else:
        st.warning("Por favor escribe un mensaje antes de enviar.")

# Mostrar historial
st.subheader("Historial de conversación:")
for chat in st.session_state.contexto:
    if chat['role'] == 'user':
        st.markdown(f"🧑 **Usuario:** {chat['content']}")
    elif chat['role'] == 'assistant':
        st.markdown(f"🤖 **Asistente:** {chat['content']}")

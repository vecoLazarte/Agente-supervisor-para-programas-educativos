# 🧠 Agente Supervisor para Programas Educativos

Repositorio para una aplicación de IA generativa enfocada en recomendaciones de programas de posgrado. Este agente permite verificar si los programas educativos de interés están alineados con las tendencias actuales y proporciona acceso a información como el presupuesto promedio, a través de una base de datos de ingresos y gastos.

## 🎯 Objetivo General

Diseñar y construir un agente inteligente especializado, capaz de:

- 🛠️ Utilizar múltiples herramientas personalizadas en LangChain.
- 🤖 Llamar al agente correspondiente según la tarea de forma autónoma y eficiente.
- 🌐 Incluir opcionalmente una interfaz web (ej. Gradio o Streamlit).

## 1. Diagrama de Arquitectura

El sistema permite que un egresado interactúe con el agente mediante lenguaje natural para conocer si los programas educativos en los que está interesado se adecuan a las tendencias actuales. El agente puede:

- Llamar al **agente de tendencias** para conocer los subcampos del área de interés que son altamente relevantes en la actualidad.
- Llamar al **agente SQL** para acceder a información personal del usuario como sus ingresos, gastos y programas educativos de interés.
- Llamar al **agente selector** para ver qué programas educativos de la base de datos se alinean con las tendencias identificadas.

Todo el flujo se realiza mediante un agente supervisado de LangChain, usando herramientas personalizadas y memoria contextual.

## 2. Descripción de Herramientas y Funciones

### 2.1 Agente de Tendencias

- **Rol:** Investigador experto que analiza artículos científicos recientes (especialmente en Arxiv) para identificar subcampos emergentes y tendencias relevantes en el ámbito profesional.
- **Herramientas que usa:** Utiliza una herramienta conectada a Arxiv para buscar publicaciones actuales y detectar cuáles son los temas con mayor proyección.

### 2.2 Agente SQL

- **Rol:** Especialista en análisis de datos que se encarga de consultar una base de datos con información sobre programas educativos, ingresos y gastos.
- **Herramientas principales:**
  - `get_schema()`: Para conocer la estructura de la base de datos.
  - `generar_sql()`: Para construir la consulta SQL correcta.
  - `run_query()`: Para ejecutar la consulta.
  - `generar_respuesta()`: Para traducir los resultados a lenguaje natural.

### 2.3 Agente Selector

- **Rol:** Asesor académico encargado de alinear las tendencias detectadas por el **agente de tendencias** con los programas disponibles identificados por el **agente SQL**.

## 3. Instrucciones de Ejecución

### 3.1 Ejecutar en Google Colab o Localmente

1. Clonar este repositorio o abrir el archivo `Proyecto_Luis_Lazarte22.ipynb`.
2. Instalar **PGAdmin 4** y **PostgreSQL**.
3. Importar las tablas de ingresos, gastos y programas educativos en PGAdmin 4.
4. Tener dos archivos `.txt`:
   - Uno con la API Key de OpenAI.
   - Otro con la cadena de conexión a la base de datos (se incluye un ejemplo referencial).

# Dashboard Máquinas - Hilandería

## Cómo correrlo

1. Instala dependencias:
   pip install -r requirements.txt

2. Corre la app:
   streamlit run app.py

3. En el navegador que se abre, sube los dos CSV que descargas por VNC:
   - Archivo de Producción (Continua_N_X...)
   - Archivo de Paros (PARO_ORD_Continua_N_X...)

## Qué muestra

- Semáforo verde/rojo por máquina, basado en el último registro
  de paro (si está "abierto" = Fin vacío, esa es la máquina ahora mismo)
- Eficiencia del turno más reciente registrado
- Tendencia de eficiencia por día
- Pareto de motivos de paro (horas acumuladas por causa)

## Próximo paso (automatización)

Por ahora subes los CSV manualmente. Cuando tengas acceso de red (SMB)
a la carpeta del contador, o una tarea programada que envíe el archivo
automáticamente, este mismo dashboard se puede conectar a Firebase para
que se actualice solo, sin subir archivos a mano.

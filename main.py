name: Actualizar Activos de Datos
on:
  schedule:
    - cron: '0 */6 * * *' # Se ejecuta cada 6 horas
  workflow_dispatch:      # Permite ejecución manual desde la pestaña Actions

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: 'true' # Elimina avisos de versiones antiguas

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout de repositorio
        uses: actions/checkout@v4

      - name: Configurar entorno de ejecucion
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instalar librerias necesarias
        run: pip install requests

      - name: Ejecutar motor de procesamiento
        run: python main.py

      - name: Sincronizar cambios en el repositorio
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add styles.m3u
          # Verifica si hay cambios antes de intentar hacer el commit
          if git diff --quiet && git diff --staged --quiet; then
            echo "No se detectaron cambios en los activos."
          else
            git commit -m "Update system assets"
            git push
          fi

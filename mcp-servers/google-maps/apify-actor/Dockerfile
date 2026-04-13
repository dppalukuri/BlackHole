# Build context: google-maps/ root (set via dockerContextDir in actor.json)
FROM apify/actor-python:3.12

# Install Playwright and dependencies
RUN pip install --no-cache-dir playwright playwright-stealth apify \
    && playwright install chromium --with-deps

# Copy google-maps source
COPY --chown=myuser:myuser scraper.py ./
COPY --chown=myuser:myuser enrichment.py ./
COPY --chown=myuser:myuser models.py ./
COPY --chown=myuser:myuser export.py ./
COPY --chown=myuser:myuser retry.py ./
COPY --chown=myuser:myuser stealth_browser.py ./

# Copy Actor source
COPY --chown=myuser:myuser apify-actor/src/ ./src/
COPY --chown=myuser:myuser apify-actor/.actor/ ./.actor/

CMD python3 -m src

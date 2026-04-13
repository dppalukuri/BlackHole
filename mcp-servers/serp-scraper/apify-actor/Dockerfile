# Build context: serp-scraper/ root (set via dockerContextDir in actor.json)
FROM apify/actor-python:3.12

RUN pip install --no-cache-dir playwright playwright-stealth apify \
    && playwright install chromium --with-deps

# Copy serp-scraper source
COPY --chown=myuser:myuser scraper.py ./
COPY --chown=myuser:myuser models.py ./
COPY --chown=myuser:myuser stealth_browser.py ./

# Copy Actor source
COPY --chown=myuser:myuser apify-actor/src/ ./src/
COPY --chown=myuser:myuser apify-actor/.actor/ ./.actor/

CMD python3 -m src
